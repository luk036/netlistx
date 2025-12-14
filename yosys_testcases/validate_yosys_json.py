import json
from jsonschema import validate
import networkx as nx

# from typing import Dict, List, Any, Set, Tuple
import sys
import os

# Add the src directory to the path to import Netlist
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from netlistx.netlist import Netlist


def read_yosys_json(filename: str) -> Netlist:
    """
    Read a Yosys JSON file and convert it to a Netlist object.

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
    nets_set = set()  # net IDs

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

    # Collect all nets from ports and netnames
    all_nets = set()

    # Nets from ports
    for port_name, port_info in module_data["ports"].items():
        for net_id in port_info["bits"]:
            all_nets.add(net_id)

    # Nets from netnames
    if "netnames" in module_data:
        for netname, netinfo in module_data["netnames"].items():
            for net_id in netinfo["bits"]:
                all_nets.add(net_id)

    # Also collect nets from cell connections
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


# Load schema and data
with open("yosys_schema.json") as f:
    schema = json.load(f)
with open("sphere_netlist.json") as f:
    data = json.load(f)

# Validate
validate(instance=data, schema=schema)

# Example usage of read_yosys_json()
if __name__ == "__main__":
    print("Testing read_yosys_json() function...")
    try:
        netlist = read_yosys_json("sphere_netlist.json")
        print("Successfully loaded netlist from sphere_netlist.json")
        print(f"  Modules: {netlist.number_of_modules()}")
        print(f"  Nets: {netlist.number_of_nets()}")
        print(f"  Total nodes: {netlist.number_of_nodes()}")
        print(f"  Pins (edges): {netlist.number_of_pins()}")
        print(f"  Pads (I/O ports): {netlist.num_pads}")
    except Exception as e:
        print(f"Error: {e}")
