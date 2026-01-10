from netlistx.graph_algo import min_maximal_independant_set, min_vertex_cover_fast
from netlistx.netlist import create_random_hgraph


def test_stress_min_vertex_cover() -> None:
    """
    Test min_vertex_cover_fast with a large random graph.
    """
    num_modules = 1000
    num_nets = 1000
    hgraph = create_random_hgraph(num_modules, num_nets)
    weight = {i: 1 for i in hgraph.ugraph}
    coverset, cost = min_vertex_cover_fast(hgraph.ugraph, weight)
    assert cost > 0
    assert len(coverset) > 0


def test_stress_min_maximal_independent_set() -> None:
    """
    Test min_maximal_independant_set with a large random graph.
    """
    num_modules = 1000
    num_nets = 1000
    hgraph = create_random_hgraph(num_modules, num_nets)
    weight = {i: 1 for i in hgraph.ugraph}
    indset, cost = min_maximal_independant_set(hgraph.ugraph, weight)
    assert cost > 0
    assert len(indset) > 0
