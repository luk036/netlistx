from netlistx.netlist import create_drawf
from netlistx.graph_algo import min_vertex_cover_fast, min_maximal_independant_set
from netlistx.cover import min_vertex_cover, min_cycle_cover, min_odd_cycle_cover


def test_min_vertex_cover():
    hyprgraph = create_drawf()
    weight = dict()

    for node in hyprgraph.gra:
        weight[node] = 1
        # covset[node] = False

    _, rslt = min_vertex_cover(hyprgraph.gra, weight)
    assert rslt == 9


def test_min_vertex_cover_fast():
    hyprgraph = create_drawf()
    weight = dict()

    for node in hyprgraph.gra:
        weight[node] = 1
        # covset[node] = False

    _, rslt = min_vertex_cover_fast(hyprgraph.gra, weight)
    assert rslt == 8


def test_min_maximal_independant_set():
    hyprgraph = create_drawf()
    weight = dict()

    for node in hyprgraph.gra:
        weight[node] = 1

    _, rslt = min_maximal_independant_set(hyprgraph.gra, weight)
    assert rslt == 7


def test_min_cycle_cover():
    hyprgraph = create_drawf()
    weight = dict()

    for node in hyprgraph.gra:
        weight[node] = 1
        # covset[node] = False

    _, rslt = min_cycle_cover(hyprgraph.gra, weight)
    assert rslt == 3


def test_min_odd_cycle_cover():
    hyprgraph = create_drawf()
    weight = dict()

    for node in hyprgraph.gra:
        weight[node] = 1
        # covset[node] = False

    _, rslt = min_odd_cycle_cover(hyprgraph.gra, weight)
    assert rslt == 0
