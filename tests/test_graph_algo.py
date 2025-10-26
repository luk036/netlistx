from netlistx.cover import min_cycle_cover, min_odd_cycle_cover, min_vertex_cover
from netlistx.graph_algo import min_maximal_independant_set, min_vertex_cover_fast


def test_min_vertex_cover(drawf_graph):
    weight = {node: 1 for node in drawf_graph.ugraph}
    _, rslt = min_vertex_cover(drawf_graph.ugraph, weight)
    assert rslt == 9


def test_min_vertex_cover_fast(drawf_graph):
    weight = {node: 1 for node in drawf_graph.ugraph}
    _, rslt = min_vertex_cover_fast(drawf_graph.ugraph, weight)
    assert rslt == 8


def test_min_vertex_cover_fast_weighted(drawf_graph):
    weight = {node: 2 for node in drawf_graph.ugraph}
    _, rslt = min_vertex_cover_fast(drawf_graph.ugraph, weight)
    assert rslt == 16


def test_min_maximal_independant_set(drawf_graph):
    weight = {node: 1 for node in drawf_graph.ugraph}
    _, rslt = min_maximal_independant_set(drawf_graph.ugraph, weight)
    assert rslt == 7


def test_min_maximal_independant_set_weighted(drawf_graph):
    weight = {node: 2 for node in drawf_graph.ugraph}
    _, rslt = min_maximal_independant_set(drawf_graph.ugraph, weight)
    assert rslt == 14


def test_min_cycle_cover(drawf_graph):
    weight = {node: 1 for node in drawf_graph.ugraph}
    _, rslt = min_cycle_cover(drawf_graph.ugraph, weight)
    assert rslt == 3


def test_min_odd_cycle_cover(drawf_graph):
    weight = {node: 1 for node in drawf_graph.ugraph}
    _, rslt = min_odd_cycle_cover(drawf_graph.ugraph, weight)
    assert rslt == 0
