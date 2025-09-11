import json

from networkx.readwrite import json_graph

from netlistx.netlist import (
    create_drawf,
    create_inverter,
    create_random_hgraph,
    create_test_netlist,
    read_json,
)


def test_inverter():
    hyprgraph = create_inverter()
    assert hyprgraph.number_of_modules() == 3
    assert hyprgraph.number_of_nets() == 2
    assert hyprgraph.number_of_nodes() == 5
    assert hyprgraph.number_of_pins() == 4
    assert hyprgraph.get_max_degree() == 2
    assert isinstance(hyprgraph.module_weight, dict)


def test_netlist():
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


def test_drawf():
    hyprgraph = create_drawf()
    assert hyprgraph.number_of_modules() == 7
    assert hyprgraph.number_of_nets() == 6
    assert hyprgraph.number_of_pins() == 14
    assert hyprgraph.get_max_degree() == 3
    # assert hyprgraph.get_max_net_degree() == 3
    # assert not hyprgraph.has_fixed_modules
    # assert hyprgraph.get_module_weight_by_id(1) == 3


def test_random_hgraph():
    hyprgraph = create_random_hgraph(30, 26)
    assert hyprgraph.number_of_modules() == 30
    assert hyprgraph.number_of_nets() == 26


def test_json():
    # hyprgraph = create_drawf()
    # data = json_graph.node_link_data(hyprgraph.ugraph)
    # with open('testcases/drawf.json', 'w') as fw:
    #     json.dump(data, fw, indent=1)
    with open("testcases/drawf.json", "r") as fr:
        data2 = json.load(fr)
    ugraph = json_graph.node_link_graph(data2)
    assert ugraph.number_of_nodes() == 13
    assert ugraph.graph["num_modules"] == 7
    assert ugraph.graph["num_nets"] == 6
    assert ugraph.graph["num_pads"] == 3


def test_json2():
    with open("testcases/p1.json", "r") as fr:
        data = json.load(fr)
    ugraph = json_graph.node_link_graph(data)
    assert ugraph.number_of_nodes() == 1735
    assert ugraph.graph["num_modules"] == 833
    assert ugraph.graph["num_nets"] == 902
    assert ugraph.graph["num_pads"] == 81


def test_readjson():
    hyprgraph = read_json("testcases/p1.json")
    count_2 = 0
    count_3 = 0
    count_rest = 0
    for net in hyprgraph.nets:
        deg = hyprgraph.ugraph.degree(net)
        if deg == 2:
            count_2 += 1
        elif deg == 3:
            count_3 += 1
        else:
            count_rest += 1
    print(count_2, count_3, count_rest)
    assert count_2 == 494
