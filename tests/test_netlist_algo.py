from netlistx.netlist import create_drawf
from netlistx.netlist_algo import min_maximal_matching
from netlistx.cover import min_hyper_vertex_cover


def test_min_vertex_cover():
    hyprgraph = create_drawf()
    weight = dict()

    for node in hyprgraph.modules:
        weight[node] = 1

    _, rslt = min_hyper_vertex_cover(hyprgraph, weight)
    assert rslt == 6


def test_min_maximal_matching():
    hyprgraph = create_drawf()
    weight = dict()

    for net in hyprgraph.nets:
        weight[net] = 1

    _, rslt = min_maximal_matching(hyprgraph, weight)
    assert rslt == 3
