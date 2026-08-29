"""Readers for netlist file formats (.net + .are + JSON/Yosys JSON).

Port of netlistx-cpp/source/readwrite.cpp readNetD and readAre, plus the
Yosys JSON readers (DOM and SAX) that previously lived in netlist.py.
"""

import json
from typing import List

import networkx as nx
from networkx.readwrite import json_graph

from netlistx.netlist import Netlist


def read_netd(filename: str) -> Netlist:
    """Read an IBM .net format file and return a Netlist.

    Header format: 0 numPins numNets numModules padOffset

    Each entry line: a<id> s|l [netnum]  (cell) or p<id> s|l [netnum]  (pad)
    - 's' marks the start of a new net
    - 'l' continues the current net (connections to the most recent 's' net)
    """
    with open(filename, "r") as f:
        lines = f.readlines()

    numPins = int(lines[1].strip())
    numNets = int(lines[2].strip())
    numModules = int(lines[3].strip())
    padOffset = int(lines[4].strip())

    total_nodes = numModules + numNets
    graph = nx.Graph()
    graph.add_nodes_from(range(numModules), bipartite=0)
    graph.add_nodes_from(range(numModules, total_nodes), bipartite=1)

    edgeIdx = numModules - 1
    pin_count = 0
    for line in lines[5:]:
        if pin_count >= numPins:
            break
        line = line.strip()
        if not line:
            continue
        entry = line.split()[0]
        kind = entry[0]
        node = int(entry[1:])
        if kind == "p":
            node += padOffset
        if " s " in line or line.endswith(" s") or " s\t" in line:
            edgeIdx += 1
        graph.add_edge(node, edgeIdx)
        pin_count += 1

    modules = list(range(numModules))
    net_nodes = list(range(numModules, numModules + numNets))
    hyprgraph = Netlist(graph, modules, net_nodes)
    hyprgraph.num_pads = numModules - padOffset - 1

    return hyprgraph


def read_are(hyprgraph: Netlist, filename: str) -> None:
    """Read an IBM .are format file and update module_weight in-place.

    Format: a<id> <weight> or p<id> <weight>
    For pads (p), offset is computed from num_modules - num_pads - 1.
    """
    pad_offset = hyprgraph.num_modules - hyprgraph.num_pads - 1
    module_weight: List[int] = [1] * hyprgraph.num_modules

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            entry = parts[0]
            weight = int(parts[1])
            kind = entry[0]
            node = int(entry[1:])
            if kind == "p":
                node += pad_offset
            module_weight[node] = weight

    hyprgraph.module_weight = module_weight


def read_json(filename: str) -> Netlist:
    """
    The function `read_json` reads a JSON file, converts it into a graph, and creates a netlist object
    with module and net weights.

    :param filename: The filename parameter is the name of the JSON file that contains the data you want
        to read
    :return: an object of type `Netlist`.
    """
    with open(filename, "r") as fr:
        data = json.load(fr)

    ugraph = json_graph.node_link_graph(data, edges="edges")
    num_modules = ugraph.graph["num_modules"]
    num_nets = ugraph.graph["num_nets"]
    num_pads = ugraph.graph["num_pads"]
    hyprgraph = Netlist(
        ugraph, range(num_modules), range(num_modules, num_modules + num_nets)
    )
    hyprgraph.num_pads = num_pads
    return hyprgraph


def _build_netlist_from_parts(
    cell_names: list[str],
    port_names: list[str],
    all_net_ids: set[int],
    cell_edges: list[tuple[int, int]],
    port_nets: dict[str, set[int]],
) -> Netlist:
    """Build a Netlist from parsed Yosys parts (shared phase 2 of the DOM and SAX readers).

    Node numbering:
      - Cell nodes (modules): 0 .. C-1
      - Net nodes:            C .. C+N-1
      - Port nodes:           C+N .. C+N+P-1

    where C = number of cells, N = number of nets, P = number of ports.
    """
    graph = nx.Graph()

    # Add cell nodes
    for i, name in enumerate(cell_names):
        graph.add_node(i, type="module", name=name)

    # Assign sorted net IDs to graph node IDs
    nets_list = sorted(all_net_ids)
    net_to_node: dict[int, int] = {
        net_id: len(cell_names) + i for i, net_id in enumerate(nets_list)
    }
    for net_id in nets_list:
        graph.add_node(net_to_node[net_id], type="net", net_id=net_id)

    # Add cell -> net edges
    for cid, raw_net_id in cell_edges:
        if raw_net_id in net_to_node:
            graph.add_edge(cid, net_to_node[raw_net_id])

    # Add port nodes and port -> net edges
    port_base = len(cell_names) + len(nets_list)
    port_nodes: list[int] = []
    for i, port_name in enumerate(port_names):
        pnode = port_base + i
        port_nodes.append(pnode)
        graph.add_node(pnode, type="port", name=port_name)
        for net_id in port_nets.get(port_name, set()):
            if net_id in net_to_node:
                graph.add_edge(pnode, net_to_node[net_id])

    # Build module / net lists for Netlist constructor
    module_nodes = list(range(len(cell_names)))
    all_module_nodes = module_nodes + port_nodes
    net_nodes = [net_to_node[nid] for nid in nets_list]

    graph.graph["num_modules"] = len(all_module_nodes)
    graph.graph["num_nets"] = len(net_nodes)
    graph.graph["num_pads"] = len(port_names)

    # Create Netlist object
    netlist = Netlist(graph, all_module_nodes, net_nodes)
    netlist.num_pads = len(port_names)

    # Set module weights: cells = 1, ports = 0
    module_weights: dict[int, int] = {}
    for i in range(len(cell_names)):
        module_weights[i] = 1
    for pnode in port_nodes:
        module_weights[pnode] = 0
    netlist.module_weight = module_weights

    # Mark port nodes as fixed (I/O pads)
    netlist.module_fixed = set(port_nodes)

    return netlist


def read_yosys_json(filename: str) -> Netlist:
    """
    Read a Yosys JSON file and convert it to a Netlist object.

    Uses ``json.load()`` to parse the entire JSON tree into memory
    (DOM-style parsing). See :func:`read_yosys_json_sax` for the
    streaming SAX-style alternative.

    Args:
        filename: Path to Yosys JSON file

    Returns:
        Netlist object representing the circuit
    """
    with open(filename, "r") as f:
        data = json.load(f)

    # Only the first module (typically the top module) is processed
    module_name = list(data["modules"].keys())[0]
    module_data = data["modules"][module_name]

    # Collect cells and ports in file order
    cell_names = list(module_data["cells"].keys())
    port_names = list(module_data["ports"].keys())

    # Collect all unique net IDs (port bits and netnames bits are kept as-is;
    # string constants like "0" in cell connections are skipped)
    all_net_ids: set[int] = set()
    for port_info in module_data["ports"].values():
        all_net_ids.update(port_info["bits"])
    if "netnames" in module_data:
        for netinfo in module_data["netnames"].values():
            all_net_ids.update(netinfo["bits"])

    cell_edges: list[tuple[int, int]] = []
    for i, cell_info in enumerate(module_data["cells"].values()):
        for connections in cell_info["connections"].values():
            for net_id in connections:
                if isinstance(net_id, int):
                    all_net_ids.add(net_id)
                    cell_edges.append((i, net_id))

    # Port connections
    port_nets: dict[str, set[int]] = {}
    for port_name, port_info in module_data["ports"].items():
        port_nets[port_name] = set(port_info["bits"])

    return _build_netlist_from_parts(
        cell_names, port_names, all_net_ids, cell_edges, port_nets
    )


def read_yosys_json_sax(filename: str) -> Netlist:
    """Read a Yosys JSON netlist file using SAX-style streaming parsing.

    Uses ``ijson`` to process the file as a stream of JSON events
    without loading the full document tree into memory. This is
    the JSON equivalent of XML's SAX parsing model — suitable for
    large netlists where memory footprint matters.

    The function performs a single pass over the file, collecting
    cell names, port names, net IDs, and connectivity as it streams,
    then assembles the final :class:`Netlist` in memory.

    Args:
        filename: Path to Yosys JSON netlist file.

    Returns:
        Netlist object representing the circuit.

    Raises:
        ImportError: If ``ijson`` is not installed.
        FileNotFoundError: If *filename* does not exist.
    """
    import ijson  # type: ignore[import-untyped]

    # ── Phase 1: streaming collection ────────────────────────────────
    cell_names: list[str] = []  # ordered list of cell names
    cell_idx: dict[str, int] = {}  # cell name → module ID
    all_net_ids: set[int] = set()  # every integer net ID seen
    port_names: list[str] = []  # ordered list of port names
    port_nets: dict[str, set[int]] = {}  # port name → connected net IDs
    cell_edges: list[tuple[int, int]] = []  # (cell_id, raw_net_id)

    # SAX state variables (updated during event stream processing)
    _current_cell: str | None = None
    _current_port: str | None = None

    # Only process the first module (matching DOM parser behaviour)
    _first_module: str | None = None
    _in_first_module: bool = False

    with open(filename, "rb") as f:
        parser = ijson.parse(f)

        for prefix, event, value in parser:
            # Ignore the "creator" field and other top-level keys
            if _first_module is None:
                if prefix == "modules" and event == "map_key":
                    _first_module = value  # type: ignore[assignment]
                    _in_first_module = True
                continue

            # Detect when we enter / leave the first module's map
            if prefix == f"modules.{_first_module}":
                if event == "end_map":
                    break  # finished the first module — stop processing
                continue  # start_map / map_key for module-level keys

            # Skip events outside the first module
            if not _in_first_module:
                continue

            # ── detect cell names ────────────────────────────────
            if ".cells" in prefix and prefix.endswith(".cells") and event == "map_key":
                _current_cell = value  # type: ignore[assignment]
                if _current_cell not in cell_idx:
                    cell_idx[_current_cell] = len(cell_names)
                    cell_names.append(_current_cell)

            # ── detect port names ────────────────────────────────
            elif (
                ".ports" in prefix and prefix.endswith(".ports") and event == "map_key"
            ):
                _current_port = value  # type: ignore[assignment]
                if _current_port not in port_nets:
                    port_nets[_current_port] = set()
                    port_names.append(_current_port)

            # ── cell connection net IDs ──────────────────────────
            elif (
                ".connections." in prefix
                and prefix.endswith(".item")
                and event == "number"
                and isinstance(value, int)
            ):
                if _current_cell is not None and _current_cell in cell_idx:
                    cell_edges.append((cell_idx[_current_cell], value))
                    all_net_ids.add(value)

            # ── port bit net IDs ─────────────────────────────────
            elif (
                ".ports." in prefix
                and ".bits.item" in prefix
                and event == "number"
                and isinstance(value, int)
            ):
                all_net_ids.add(value)
                if _current_port is not None:
                    port_nets[_current_port].add(value)

            # ── netnames bit net IDs ─────────────────────────────
            elif (
                ".netnames." in prefix
                and ".bits.item" in prefix
                and event == "number"
                and isinstance(value, int)
            ):
                all_net_ids.add(value)

            # ── reset state on object boundaries ─────────────────
            elif (
                ".cells." in prefix and event == "end_map" and _current_cell is not None
            ):
                parts = prefix.split(".")
                if parts[-1] == _current_cell:
                    _current_cell = None

            elif (
                ".ports." in prefix and event == "end_map" and _current_port is not None
            ):
                parts = prefix.split(".")
                if parts[-1] == _current_port:
                    _current_port = None

    # ── Phase 2: build the graph from collected data ─────────────────
    return _build_netlist_from_parts(
        cell_names, port_names, all_net_ids, cell_edges, port_nets
    )
