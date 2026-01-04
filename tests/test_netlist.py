from typing import Any

from networkx.readwrite import json_graph

from netlistx.netlist import (
    create_inverter,
    create_random_hgraph,
    create_test_netlist,
)


def test_inverter() -> None:
    hyprgraph = create_inverter()
    assert hyprgraph.number_of_modules() == 3
    assert hyprgraph.number_of_nets() == 2
    assert hyprgraph.number_of_nodes() == 5
    assert hyprgraph.number_of_pins() == 4
    assert hyprgraph.get_max_degree() == 2
    assert isinstance(hyprgraph.module_weight, dict)


def test_netlist() -> None:
    hyprgraph = create_test_netlist()
    assert hyprgraph.number_of_modules() == 3
    assert hyprgraph.number_of_nets() == 3
    assert hyprgraph.number_of_nodes() == 6
    assert hyprgraph.number_of_pins() == 6
    assert hyprgraph.get_max_degree() == 3
    # assert hyprgraph.get_max_net_degree() == 3
    # assert not hyprgraph.has_fixed_modules
    # assert hyprgraph.get_module_weight_by_id(0) == 533
    assert isinstance(hyprgraph.module_weight, dict)


def test_drawf(drawf_graph: Any) -> None:
    assert drawf_graph.number_of_modules() == 7
    assert drawf_graph.number_of_nets() == 6
    assert drawf_graph.number_of_pins() == 14
    assert drawf_graph.get_max_degree() == 3
    # assert hyprgraph.get_max_net_degree() == 3
    # assert not hyprgraph.has_fixed_modules
    # assert hyprgraph.get_module_weight_by_id(1) == 3


def test_random_hgraph() -> None:
    hyprgraph = create_random_hgraph(30, 26)
    assert hyprgraph.number_of_modules() == 30
    assert hyprgraph.number_of_nets() == 26


def test_json(drawf_json: Any) -> None:
    ugraph = json_graph.node_link_graph(drawf_json)
    assert ugraph.number_of_nodes() == 13
    assert ugraph.graph["num_modules"] == 7
    assert ugraph.graph["num_nets"] == 6
    assert ugraph.graph["num_pads"] == 3


def test_json2(p1_json: Any) -> None:
    ugraph = json_graph.node_link_graph(p1_json)
    assert ugraph.number_of_nodes() == 1735
    assert ugraph.graph["num_modules"] == 833
    assert ugraph.graph["num_nets"] == 902
    assert ugraph.graph["num_pads"] == 81


def test_readjson(p1_graph: Any) -> None:
    count_2 = 0
    count_3 = 0
    count_rest = 0
    for net in p1_graph.nets:
        deg = p1_graph.ugraph.degree(net)
        if deg == 2:
            count_2 += 1
        elif deg == 3:
            count_3 += 1
        else:
            count_rest += 1
    print(count_2, count_3, count_rest)
    assert count_2 == 494


def test_netlist_module_weight_dict() -> None:
    """Test netlist with dictionary module_weight to cover lines 217, 228-230."""
    from netlistx.netlist import Netlist
    import networkx as nx

    # Create a simple netlist
    G = nx.Graph()
    G.add_nodes_from([0, 1, 2, 3, 4])
    G.add_edges_from([(0, 3), (1, 3), (2, 4), (3, 4)])
    G.graph["num_modules"] = 3
    G.graph["num_nets"] = 2
    G.graph["num_pads"] = 0

    # Create netlist and set dictionary module_weight as attribute
    modules = [0, 1, 2]
    nets = [3, 4]
    netlist = Netlist(G, modules, nets)
    netlist.module_weight = {0: 5, 1: 10, 2: 15}

    # Test get_module_weight method with dict module_weight
    # When modules is a list, the module at index v is used as the key
    assert netlist.get_module_weight(0) == 5  # modules[0] = 0, module_weight[0] = 5
    assert netlist.get_module_weight(1) == 10  # modules[1] = 1, module_weight[1] = 10
    assert netlist.get_module_weight(2) == 15  # modules[2] = 2, module_weight[2] = 15
    # Test default weight for non-existent module - this will raise IndexError
    # as we're trying to access modules[99] which doesn't exist


def test_netlist_module_weight_dict_range() -> None:
    """Test netlist with dictionary module_weight and range modules."""
    from netlistx.netlist import Netlist
    import networkx as nx

    # Create a simple netlist
    G = nx.Graph()
    G.add_nodes_from([0, 1, 2, 3, 4])
    G.add_edges_from([(0, 3), (1, 3), (2, 4), (3, 4)])
    G.graph["num_modules"] = 3
    G.graph["num_nets"] = 2
    G.graph["num_pads"] = 0

    # Create netlist with range modules and dict module_weight
    modules = range(3)  # 0, 1, 2
    nets = [3, 4]
    netlist = Netlist(G, modules, nets)
    netlist.module_weight = {0: 5, 1: 10, 2: 15}

    # Test get_module_weight method with dict module_weight and range modules
    assert netlist.get_module_weight(0) == 5  # module_weight[0] = 5
    assert netlist.get_module_weight(1) == 10  # module_weight[1] = 10
    assert netlist.get_module_weight(2) == 15  # module_weight[2] = 15
    # Test default weight for non-existent module
    assert netlist.get_module_weight(99) == 1  # module_weight.get(99, 1) = 1


def test_netlist_module_weight_list() -> None:
    """Test netlist with list module_weight to cover line 232."""
    from netlistx.netlist import Netlist
    import networkx as nx

    # Create a simple netlist
    G = nx.Graph()
    G.add_nodes_from([0, 1, 2, 3, 4])
    G.add_edges_from([(0, 3), (1, 3), (2, 4), (3, 4)])
    G.graph["num_modules"] = 3
    G.graph["num_nets"] = 2
    G.graph["num_pads"] = 0

    # Create netlist and set list module_weight as attribute
    modules = [0, 1, 2]
    nets = [3, 4]
    netlist = Netlist(G, modules, nets)
    netlist.module_weight = [5, 10, 15]

    # Test get_module_weight method with list module_weight
    assert netlist.get_module_weight(0) == 5
    assert netlist.get_module_weight(1) == 10
    assert netlist.get_module_weight(2) == 15


def test_netlist_module_weight_none() -> None:
    """Test netlist with None module_weight to cover line 232."""
    from netlistx.netlist import Netlist
    import networkx as nx

    # Create a simple netlist
    G = nx.Graph()
    G.add_nodes_from([0, 1, 2, 3, 4])
    G.add_edges_from([(0, 3), (1, 3), (2, 4), (3, 4)])
    G.graph["num_modules"] = 3
    G.graph["num_nets"] = 2
    G.graph["num_pads"] = 0

    # Create netlist and set None module_weight as attribute
    modules = [0, 1, 2]
    nets = [3, 4]
    netlist = Netlist(G, modules, nets)
    netlist.module_weight = None

    # Test get_module_weight method with None module_weight
    assert netlist.get_module_weight(0) == 1
    assert netlist.get_module_weight(1) == 1
    assert netlist.get_module_weight(2) == 1
