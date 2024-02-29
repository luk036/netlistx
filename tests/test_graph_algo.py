from netlistx.cover import min_cycle_cover, min_odd_cycle_cover, min_vertex_cover
from netlistx.graph_algo import min_maximal_independant_set, min_vertex_cover_fast
from netlistx.netlist import create_drawf


def test_min_vertex_cover():
    hyprgraph = create_drawf()
    weight = dict()

    for node in hyprgraph.ugraph:
        weight[node] = 1
        # covset[node] = False

    _, rslt = min_vertex_cover(hyprgraph.ugraph, weight)
    assert rslt == 9


def test_min_vertex_cover_fast():
    hyprgraph = create_drawf()
    weight = dict()

    for node in hyprgraph.ugraph:
        weight[node] = 1
        # covset[node] = False

    _, rslt = min_vertex_cover_fast(hyprgraph.ugraph, weight)
    assert rslt == 8


def test_min_maximal_independant_set():
    hyprgraph = create_drawf()
    weight = dict()

    for node in hyprgraph.ugraph:
        weight[node] = 1

    _, rslt = min_maximal_independant_set(hyprgraph.ugraph, weight)
    assert rslt == 7


def test_min_cycle_cover():
    hyprgraph = create_drawf()
    weight = dict()

    for node in hyprgraph.ugraph:
        weight[node] = 1
        # covset[node] = False

    _, rslt = min_cycle_cover(hyprgraph.ugraph, weight)
    assert rslt == 3


def test_min_odd_cycle_cover():
    hyprgraph = create_drawf()
    weight = dict()

    for node in hyprgraph.ugraph:
        weight[node] = 1
        # covset[node] = False

    _, rslt = min_odd_cycle_cover(hyprgraph.ugraph, weight)
    assert rslt == 0
