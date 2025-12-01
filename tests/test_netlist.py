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
