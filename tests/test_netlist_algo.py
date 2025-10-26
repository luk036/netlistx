from netlistx.cover import min_hyper_vertex_cover
from netlistx.netlist_algo import min_maximal_matching


def test_min_vertex_cover(drawf_graph):
    weight = {node: 1 for node in drawf_graph.modules}
    _, rslt = min_hyper_vertex_cover(drawf_graph, weight)
    assert rslt == 6


def test_min_maximal_matching(drawf_graph):
    weight = {net: 1 for net in drawf_graph.nets}
    _, rslt = min_maximal_matching(drawf_graph, weight)
    assert rslt == 3


def test_min_maximal_matching2(p1_graph):
    weight = {net: 1 for net in p1_graph.nets}
    _, rslt = min_maximal_matching(p1_graph, weight)
    assert rslt == 239
