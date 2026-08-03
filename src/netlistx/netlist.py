"""
Netlist.py

This code defines a set of classes and functions for working with netlists, which
are representations of electronic circuits. The main purpose of this code is to
provide tools for creating, manipulating, and analyzing netlists.

.. svgbob::
   :align: center

      Cell1 ──── NetA ──── Cell2
        │                    │
        │                    │
      NetB                NetC
        │                    │
        │                    │
      Cell3 ──── NetD ──── Cell4

The code doesn't take any direct inputs or produce any outputs on its own.
Instead, it defines classes and functions that can be used by other parts of a
program to work with netlists.

The main class in this code is the Netlist class. It represents a netlist as a
graph, where modules (like electronic components) are connected by nets (like
wires). The Netlist class takes three inputs when created: a graph representing
the connections, a list of modules, and a list of nets.

The Netlist class provides several methods to get information about the netlist,
such as the number of modules, nets, nodes, and pins. It also allows you to get
the weight of modules and nets, which could represent things like the size or
importance of components in the circuit.

The code includes several helper functions to create specific types of netlists.
For example, create_inverter() creates a netlist representing a simple inverter
circuit, while create_random_hgraph() creates a random netlist with a specified
number of modules and nets.

The code uses graph theory concepts to represent the netlist. It uses the
NetworkX library to handle the graph operations. The graph is represented as
nodes (modules and nets) connected by edges (connections between modules and
nets).

One important aspect of the code is how it handles the weights of modules and
nets. It uses a RepeatArray class (which is not defined in this file) to
efficiently store weights when many components have the same weight.

The code also includes functions for reading netlists from JSON files and for
creating specific test netlists. These functions could be useful for testing or
demonstrating the capabilities of the Netlist class.

Overall, this code provides a foundation for working with netlists in Python.
It allows programmers to create, manipulate, and analyze netlists, which could
be useful in electronic design automation tools or circuit analysis software.
"""

import json
import random
from typing import Any, Dict, Iterator, List, Optional, Union

import networkx as nx
from mywheel.array_like import RepeatArray  # type: ignore
from mywheel.map_adapter import MapAdapter  # type: ignore
from networkx.algorithms import bipartite
from networkx.readwrite import json_graph


class SimpleGraph(nx.Graph):
    r"""
    The `SimpleGraph` class is a subclass of `nx.Graph` that defines default attributes for edges and
    nodes.

    .. svgbob::
       :align: center

          o-----o
         / \   /
        /   \ /
       o-----o

    """

    all_edge_dict = {"weight": 1}

    def single_edge_dict(self) -> Dict:
        """Returns the default edge attribute dictionary."""
        return self.all_edge_dict

    edge_attr_dict_factory = single_edge_dict  # type: ignore
    node_attr_dict_factory = single_edge_dict  # type: ignore


# The TinyGraph class is a subclass of nx.Graph that initializes a graph with a specified number of
# nodes and provides methods for creating node dictionaries and adjacency list dictionaries.
class TinyGraph(nx.Graph):
    r"""
    The `TinyGraph` class is a subclass of `nx.Graph` that initializes a graph with a specified number
    of nodes and provides methods for creating node dictionaries and adjacency list dictionaries.

    .. svgbob::
       :align: center

          o-o
         / /
        o-o

    """

    num_nodes = 0

    def cheat_node_dict(self) -> "MapAdapter":
        """Returns a MapAdapter for node dictionaries."""
        return MapAdapter([dict() for _ in range(self.num_nodes)])

    def cheat_adjlist_outer_dict(self) -> "MapAdapter":
        """Returns a MapAdapter for adjacency list outer dictionaries."""
        return MapAdapter([dict() for _ in range(self.num_nodes)])

    node_dict_factory = cheat_node_dict
    adjlist_outer_dict_factory = cheat_adjlist_outer_dict

    def init_nodes(self, n: int) -> None:
        self.num_nodes = n
        self._node = self.cheat_node_dict()
        self._adj = self.cheat_adjlist_outer_dict()


# The `Netlist` class represents a netlist, which is a collection of modules and nets in a graph
# structure, and provides various properties and methods for working with the netlist.
#
# .. svgbob::
#
#    +---+     +---+
#    | M1|-----| N1|
#    +---+     +---+
#      |         |
#      +---------+
#      |         |
#    +---+     +---+
#    | M2|-----| N2|
#    +---+     +---+
#
class Netlist:
    num_pads: int = 0
    cost_model: int = 0

    def __init__(
        self,
        ugraph: nx.Graph,
        modules: Union[range, List[Any]],
        nets: Union[range, List[Any]],
    ) -> None:
        r"""
        The function initializes an object with a graph, modules, and nets, and calculates some properties
        of the graph.

        :param ugraph: The parameter `ugraph` is a graph object of type `nx.Graph`. It represents the graph
            structure of the system
        :type ugraph: nx.Graph
        :param modules: The `modules` parameter is a list or range object that represents the modules in the
            graph. Each module is a node in the graph
        :type modules: Union[range, List[Any]]
        :param nets: The `nets` parameter is a list or range that represents the nets in the graph. A net is
            a connection between two or more modules
        :type nets: Union[range, List[Any]]

        .. svgbob::
           :align: center

              +---+
              | M |
              +---+
                |
              +---+
              | N |
              +---+

        """
        self.ugraph = ugraph
        self.modules = modules
        self.nets = nets

        self.num_modules = len(modules)
        self.num_nets = len(nets)
        self.module_weight: Union[RepeatArray, Dict, List[int]] = RepeatArray(
            1, self.num_modules
        )
        self.module_fixed: set = set()
        self.net_weight: Optional[Union[Dict, List[int]]] = None
        self.max_degree = max(self.ugraph.degree[cell] for cell in modules)

    def number_of_modules(self) -> int:
        """
        The function "number_of_modules" returns the number of modules.
        :return: The method is returning the value of the attribute `num_modules`.
        """
        return self.num_modules

    def number_of_nets(self) -> int:
        """
        The function "number_of_nets" returns the number of nets.
        :return: The number of nets.
        """
        return self.num_nets

    def number_of_nodes(self) -> int:
        """
        The function "number_of_nodes" returns the number of nodes in a graph.
        :return: The number of nodes in the graph.
        """
        return self.ugraph.number_of_nodes()

    def number_of_pins(self) -> int:
        """
        The function `number_of_pins` returns the number of edges in a graph.
        :return: The number of edges in the graph.
        """
        return self.ugraph.number_of_edges()

    def get_max_degree(self) -> int:
        """
        The function `get_max_degree` returns the maximum degree of nodes in a graph.
        :return: the maximum degree of the nodes in the graph.
        """
        return max(self.ugraph.degree[cell] for cell in self.modules)

    def get_module_weight(self, v: int) -> int:
        """
        The function `get_module_weight` returns the weight of a module given its
        index.

        :param v: The parameter `v` in the `get_module_weight` function is of type
            `size_t`. It represents the index or key of the module weight that you
            want to retrieve

        :return: the value of `self.module_weight[v]`.
        """
        if isinstance(self.module_weight, RepeatArray):
            return self.module_weight[v]
        elif isinstance(self.module_weight, dict):
            # If module_weight is a dictionary, we need to handle it differently
            # Convert the modules list to get the value by index
            if isinstance(self.modules, list):
                module_key = self.modules[v]
                return self.module_weight.get(
                    module_key, 1
                )  # default to 1 if not found
            else:
                # If modules is a range, assume direct indexing
                return self.module_weight.get(v, 1)
        elif isinstance(self.module_weight, list):
            return self.module_weight[v]
        else:
            return 1  # default value

    def get_net_weight(self, _: Any) -> int:
        """
        The function `get_net_weight` returns an integer value.

        :param _: The underscore (_) in the function signature is a convention in
            Python to indicate that the parameter is not used within the function.
            It is often used when a parameter is required by the function signature
            but not actually used within the function's implementation. In this case,
            the underscore (_) is used as a placeholder for

        :return: An integer value of 1 is being returned.
        """
        return 1

    def __iter__(self) -> Iterator:
        """
        The function returns an iterator over all modules in the Netlist.
        :return: The `iter(self.modules)` is being returned.
        """
        return iter(self.modules)


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

    # Create a bipartite graph
    graph = nx.Graph()

    # Track all nets (wire IDs) and their connections
    # In Yosys JSON, nets are identified by integer IDs
    # Cells/modules connect to nets via port connections

    # First, collect all cells/modules and nets
    modules_dict = {}  # module_name -> module_id

    # We'll process the first module (typically the top module)
    # Yosys JSON can have multiple modules, but we'll take the first one
    # as the main design
    module_name = list(data["modules"].keys())[0]
    module_data = data["modules"][module_name]

    # Add cells as module nodes
    cell_names = list(module_data["cells"].keys())
    for i, cell_name in enumerate(cell_names):
        modules_dict[cell_name] = i
        graph.add_node(i, type="module", name=cell_name)

    all_nets = set()

    for port_name, port_info in module_data["ports"].items():
        for net_id in port_info["bits"]:
            all_nets.add(net_id)

    if "netnames" in module_data:
        for netname, netinfo in module_data["netnames"].items():
            for net_id in netinfo["bits"]:
                all_nets.add(net_id)

    for cell_name, cell_info in module_data["cells"].items():
        for port_name, connections in cell_info["connections"].items():
            for net_id in connections:
                if isinstance(net_id, int):
                    all_nets.add(net_id)

    # Add nets as net nodes
    nets_list = sorted(list(all_nets))
    nets_dict = {net_id: i + len(cell_names) for i, net_id in enumerate(nets_list)}
    for net_id in nets_list:
        node_id = nets_dict[net_id]
        graph.add_node(node_id, type="net", net_id=net_id)

    # Add edges between cells and nets based on connections
    for cell_name, cell_info in module_data["cells"].items():
        cell_node = modules_dict[cell_name]
        for port_name, connections in cell_info["connections"].items():
            for net_id in connections:
                if isinstance(net_id, int):
                    net_node = nets_dict[net_id]
                    graph.add_edge(cell_node, net_node)

    # Also add edges for port connections (treat ports as special cells)
    # Ports are I/O and should be treated as fixed modules
    port_names = list(module_data["ports"].keys())
    for i, port_name in enumerate(port_names):
        port_node_id = len(cell_names) + len(nets_list) + i
        modules_dict[f"PORT_{port_name}"] = port_node_id
        graph.add_node(port_node_id, type="port", name=port_name)

        port_info = module_data["ports"][port_name]
        for net_id in port_info["bits"]:
            if net_id in nets_dict:
                net_node = nets_dict[net_id]
                graph.add_edge(port_node_id, net_node)

    # Create module and net lists for Netlist constructor
    module_nodes = [i for i in range(len(cell_names))]
    port_nodes = [len(cell_names) + len(nets_list) + i for i in range(len(port_names))]
    all_module_nodes = module_nodes + port_nodes
    net_nodes = [nets_dict[net_id] for net_id in nets_list]

    # Set graph properties expected by Netlist
    graph.graph["num_modules"] = len(all_module_nodes)
    graph.graph["num_nets"] = len(net_nodes)
    graph.graph["num_pads"] = len(port_names)  # Ports are pads

    # Create Netlist object
    netlist = Netlist(graph, all_module_nodes, net_nodes)
    netlist.num_pads = len(port_names)

    # Set module weights (cells have weight 1, ports have weight 0)
    module_weights = {}
    for i in range(len(cell_names)):
        module_weights[i] = 1
    for i, port_node in enumerate(port_nodes):
        module_weights[port_node] = 0

    netlist.module_weight = module_weights

    # Mark port nodes as fixed
    netlist.module_fixed = set(port_nodes)

    return netlist


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

    # Add cell → net edges
    for cid, raw_net_id in cell_edges:
        if raw_net_id in net_to_node:
            graph.add_edge(cid, net_to_node[raw_net_id])

    # Add port nodes and port → net edges
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


def create_inverter() -> Netlist:
    """
    Create a simple inverter netlist.

    The inverter consists of:
    - One AND gate (a0)
    - Two input pads (p1, p2)
    - Two nets (n0, n1)

    Net n0 connects input pad p1 to AND gate input, AND gate output.
    Net n1 connects AND gate input to output pad p2.

    :return: A Netlist representing the inverter circuit.
    :rtype: Netlist
    """
    graph = SimpleGraph()
    graph.add_nodes_from(["a0", "p1", "p2", "n0", "n1"])
    nets = ["n0", "n1"]
    modules = ["a0", "p1", "p2"]
    module_weight = {"a0": 1, "p1": 0, "p2": 0}

    graph.add_edges_from(
        [
            ("n0", "p1", {"dir": "I"}),
            ("n0", "a0", {"dir": "O"}),
            ("n1", "a0", {"dir": "I"}),
            ("n1", "p2", {"dir": "O"}),
        ]
    )
    graph.graph["num_modules"] = 3
    graph.graph["num_nets"] = 2
    graph.graph["num_pads"] = 2
    hyprgraph = Netlist(graph, modules, nets)
    hyprgraph.module_weight = module_weight  # type: ignore[assignment]
    hyprgraph.net_weight = RepeatArray(1, len(nets))  # type: ignore[assignment]
    hyprgraph.num_pads = 2
    return hyprgraph


def create_inverter2() -> Netlist:
    """
    Create a simple inverter netlist using numeric node IDs.

    Similar to create_inverter() but uses integer node IDs (0-4) instead of
    string names. This variant uses modules 0-2 and nets 3-4.

    :return: A Netlist representing the inverter circuit.
    :rtype: Netlist
    """
    graph = SimpleGraph()
    graph.add_nodes_from([0, 1, 2, 3, 4])
    nets = range(3, 5)
    modules = range(3)
    module_weight = [1, 0, 0]

    graph.add_edges_from(
        [
            (3, 1, {"dir": "I"}),
            (3, 0, {"dir": "O"}),
            (4, 0, {"dir": "I"}),
            (4, 2, {"dir": "O"}),
        ]
    )
    graph.graph["num_modules"] = 3
    graph.graph["num_nets"] = 2
    graph.graph["num_pads"] = 2
    hyprgraph = Netlist(graph, modules, nets)
    hyprgraph.module_weight = module_weight  # type: ignore[assignment]
    hyprgraph.net_weight = RepeatArray(1, len(nets))  # type: ignore[assignment]
    hyprgraph.num_pads = 2
    return hyprgraph


def create_drawf() -> Netlist:
    """
    The function `create_drawf` creates a graph and netlist object with specified nodes, edges, and
    weights.

    :return: an instance of the Netlist class, which is created using the SimpleGraph class and some
        predefined modules and nets.
    """
    ugraph = SimpleGraph()
    ugraph.add_nodes_from(
        [
            "a0",
            "a1",
            "a2",
            "a3",
            "p1",
            "p2",
            "p3",
            "n0",
            "n1",
            "n2",
            "n3",
            "n4",
            "n5",
        ]
    )
    nets = [
        "n0",
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
    ]
    modules = ["a0", "a1", "a2", "a3", "p1", "p2", "p3"]
    module_weight = {"a0": 1, "a1": 3, "a2": 4, "a3": 2, "p1": 0, "p2": 0, "p3": 0}

    ugraph.add_edges_from(
        [
            ("n0", "p1", {"dir": "I"}),
            ("n0", "a0", {"dir": "I"}),
            ("n0", "a1", {"dir": "O"}),
            ("n1", "a0", {"dir": "I"}),
            ("n1", "a2", {"dir": "I"}),
            ("n1", "a3", {"dir": "O"}),
            ("n2", "a1", {"dir": "I"}),
            ("n2", "a2", {"dir": "I"}),
            ("n2", "a3", {"dir": "O"}),
            ("n3", "a2", {"dir": "I"}),
            ("n3", "p2", {"dir": "O"}),
            ("n4", "a3", {"dir": "I"}),
            ("n4", "p3", {"dir": "O"}),
            ("n5", "p2", {"dir": "B"}),
        ]
    )
    ugraph.graph["num_modules"] = 7
    ugraph.graph["num_nets"] = 6
    ugraph.graph["num_pads"] = 3
    hyprgraph = Netlist(ugraph, modules, nets)
    hyprgraph.module_weight = module_weight  # type: ignore[assignment]
    hyprgraph.net_weight = RepeatArray(1, len(nets))  # type: ignore[assignment]
    hyprgraph.num_pads = 3
    return hyprgraph


def create_test_netlist() -> Netlist:
    """
    The function `create_test_netlist` creates a test netlist with nodes, edges, module weights, and net
    weights.
    :return: an instance of the `Netlist` class, which represents a netlist with modules and nets.
    """
    ugraph = SimpleGraph()
    ugraph.add_nodes_from(["a0", "a1", "a2", "a3", "a4", "a5"])
    module_weight = {"a0": 533, "a1": 543, "a2": 532}
    ugraph.add_edges_from(
        [
            ("a3", "a0"),
            ("a3", "a1"),
            ("a4", "a0"),
            ("a4", "a1"),
            ("a4", "a2"),
            ("a5", "a0"),  # self-loop
        ]
    )

    ugraph.graph["num_modules"] = 3
    ugraph.graph["num_nets"] = 3
    modules = ["a0", "a1", "a2"]
    nets = ["a3", "a4", "a5"]
    net_weight = RepeatArray(1, len(nets))

    hyprgraph = Netlist(ugraph, modules, nets)
    hyprgraph.module_weight = module_weight  # type: ignore[assignment]
    hyprgraph.net_weight = net_weight  # type: ignore[assignment]
    return hyprgraph


def vdc(n: int, base: int = 2) -> float:
    """Compute the n-th van der Corput sequence value.

    The van der Corput sequence is a low-discrepancy sequence that
    generates points uniformly in the [0, 1) interval by reversing
    the base-*base* representation of *n*.

    :param n: Non-negative integer index.
    :type n: int
    :param base: Numeric base for digit reversal (default: 2).
    :type base: int
    :return: The n-th van der Corput value in [0, 1).
    :rtype: float

    Examples:
        >>> vdc(0)
        0.0
        >>> vdc(1)
        0.5
        >>> vdc(2)
        0.25
        >>> vdc(3)
        0.75
    """
    vdc, denom = 0.0, 1.0
    while n:
        denom *= base
        n, remainder = divmod(n, base)
        vdc += remainder / denom
    return vdc


def vdcorput(n: int, base: int = 2) -> List[float]:
    """Generate the first *n* values of the van der Corput sequence.

    Convenience wrapper around :func:`vdc` that returns a list of
    sequence values for indices ``0`` through ``n-1``.

    :param n: Number of sequence values to generate.
    :type n: int
    :param base: Numeric base for digit reversal (default: 2).
    :type base: int
    :return: List of the first *n* van der Corput values.
    :rtype: List[float]

    Examples:
        >>> vdcorput(4)
        [0.0, 0.5, 0.25, 0.75]
    """
    return [vdc(i, base) for i in range(n)]


def form_graph(
    N: int, M: int, _: Any, eta: float, seed: Optional[int] = None
) -> nx.Graph:
    """Generate a random bipartite graph with *N* and *M* nodes.

    Uses :func:`networkx.algorithms.bipartite.random_graph` to create
    a bipartite graph where each possible edge between the two partitions
    exists independently with probability *eta*.

    :param N: Number of nodes in the first partition (modules).
    :type N: int
    :param M: Number of nodes in the second partition (nets).
    :type M: int
    :param _: Unused positional parameter (for API compatibility).
    :type _: Any
    :param eta: Edge probability for the random bipartite graph.
    :type eta: float
    :param seed: Optional random seed for reproducibility.
    :type seed: Optional[int]
    :return: A random bipartite graph.
    :rtype: nx.Graph
    """
    if seed:
        random.seed(seed)

    # connect nodes with edges
    ugraph = bipartite.random_graph(N, M, eta)
    return ugraph


def create_random_hgraph(N: int = 30, M: int = 26, eta: float = 0.1) -> Netlist:
    """
    Create a random bipartite hypergraph for testing.

    Uses van der Corput quasi-random sequences to distribute nodes
    uniformly in 2D space, then creates edges based on distance threshold.

    :param N: Number of module nodes (default: 30).
    :type N: int
    :param M: Number of net nodes (default: 26).
    :type M: int
    :param eta: Edge probability/density parameter (default: 0.1).
    :type eta: float

    :return: A Netlist with randomly distributed nodes and edges.
    :rtype: Netlist
    """
    T = N + M
    xbase = 2
    ybase = 3
    x = [i for i in vdcorput(T, xbase)]
    y = [i for i in vdcorput(T, ybase)]
    pos = zip(x, y)
    ugraph = form_graph(N, M, pos, eta, seed=5)

    ugraph.graph["num_modules"] = N
    ugraph.graph["num_nets"] = M
    hyprgraph = Netlist(ugraph, range(N), range(N, N + M))
    hyprgraph.module_weight = RepeatArray(1, N)  # type: ignore[assignment]
    hyprgraph.net_weight = RepeatArray(1, M)  # type: ignore[assignment]
    return hyprgraph
