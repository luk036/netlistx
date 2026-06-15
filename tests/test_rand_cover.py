from typing import Any

import networkx as nx

from netlistx.rand_cover import rand_hyper_vertex_cover, rand_vertex_cover


def test_rand_vertex_cover_simple() -> None:
    """Test on a simple 3-node triangle with unit weights."""
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (0, 2), (1, 2)])
    weight = {0: 1, 1: 1, 2: 1}
    soln, cost = rand_vertex_cover(ugraph, weight, seed=0)
    # Any 2 vertices cover a triangle.
    assert len(soln) == 2
    assert cost == 2
    # Verify it's a valid vertex cover
    for u, v in ugraph.edges():
        assert u in soln or v in soln


def test_rand_vertex_cover_line() -> None:
    """Test on a simple line graph (3 nodes, 2 edges)."""
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (1, 2)])
    weight = {0: 1, 1: 1, 2: 1}
    soln, cost = rand_vertex_cover(ugraph, weight, seed=1)
    # Middle node alone covers both edges
    assert len(soln) >= 1
    assert len(soln) <= 2
    # Verify it's a valid vertex cover
    for u, v in ugraph.edges():
        assert u in soln or v in soln


def test_rand_vertex_cover_star() -> None:
    """Test on a star graph."""
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (0, 2), (0, 3)])
    weight = {0: 1, 1: 1, 2: 1, 3: 1}
    soln, cost = rand_vertex_cover(ugraph, weight, seed=2)
    # Either the center (0) alone or all leaves
    assert cost >= 1
    assert cost <= 3
    # Verify it's a valid vertex cover
    for u, v in ugraph.edges():
        assert u in soln or v in soln
    # If cost is 1, center is the only vertex in the cover
    if cost == 1:
        assert soln == {0}


def test_rand_vertex_cover_weighted() -> None:
    """Test with weighted vertices to verify Pitt's probability rule."""
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1)])
    weight = {0: 100, 1: 1}
    # Run many trials to check the lighter vertex is preferred
    picks_0 = 0
    trials = 200
    for seed in range(trials):
        soln, _ = rand_vertex_cover(ugraph, weight, seed=seed)
        if 0 in soln:
            picks_0 += 1
    # Vertex 1 (weight 1) should be picked more often than vertex 0 (weight 100)
    # P(pick 0) = 1/101 ≈ 0.01, P(pick 1) ≈ 0.99
    assert picks_0 < trials * 0.1, f"Vertex 0 picked {picks_0}/{trials} times"


def test_rand_vertex_cover_empty_graph() -> None:
    """Empty graph should return empty cover."""
    ugraph = nx.Graph()
    weight: dict[int, int] = {}
    soln, cost = rand_vertex_cover(ugraph, weight, seed=0)
    assert len(soln) == 0
    assert cost == 0


def test_rand_vertex_cover_single_edge_weighted() -> None:
    """Single edge with different weights."""
    ugraph = nx.Graph()
    ugraph.add_edge(0, 1)
    weight = {0: 5, 1: 10}
    soln, cost = rand_vertex_cover(ugraph, weight, seed=42)
    # Exactly one endpoint should be selected
    assert len(soln) == 1
    assert (0 in soln and cost == 5) or (1 in soln and cost == 10)
    # Verify it's a valid vertex cover
    for u, v in ugraph.edges():
        assert u in soln or v in soln


def test_rand_vertex_cover_deterministic_seed() -> None:
    """Same seed should produce same result."""
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])
    weight = {0: 2, 1: 3, 2: 1, 3: 4}
    soln1, cost1 = rand_vertex_cover(ugraph, weight, seed=123)
    soln2, cost2 = rand_vertex_cover(ugraph, weight, seed=123)
    assert soln1 == soln2
    assert cost1 == cost2


def test_rand_vertex_cover_with_initial_coverset() -> None:
    """Test with an initial coverset."""
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (1, 2), (2, 0)])
    weight = {0: 1, 1: 1, 2: 1}
    soln, cost = rand_vertex_cover(ugraph, weight, coverset={0}, seed=42)
    # Verify initial vertex is in the cover
    assert 0 in soln
    # Verify it's a valid vertex cover
    for u, v in ugraph.edges():
        assert u in soln or v in soln


def test_rand_vertex_cover_drawf(drawf_graph: Any) -> None:
    """Test on the drawf graph fixture (from conftest)."""
    weight = {node: 1 for node in drawf_graph.ugraph}
    soln, cost = rand_vertex_cover(drawf_graph.ugraph, weight, seed=42)
    # Verify it's a valid vertex cover
    for u, v in drawf_graph.ugraph.edges():
        assert u in soln or v in soln
    # Cost should not exceed number of vertices
    assert cost <= len(drawf_graph.ugraph)
    # Cost should be at least 1 for this graph (has edges)
    assert cost >= 1


# --- Hypergraph tests ---


class MockHyprgraph:
    """Minimal mock hypergraph for testing."""

    def __init__(self, nets, ugraph):
        self.nets = nets
        self.ugraph = ugraph


def test_rand_hyper_vertex_cover_simple() -> None:
    """Single net with 2 vertices (degenerates to Pitt's edge rule)."""
    hyprgraph = MockHyprgraph(["N1"], {"N1": [0, 1]})
    weight = {0: 1, 1: 1}
    soln, cost = rand_hyper_vertex_cover(hyprgraph, weight, seed=0)
    assert len(soln) == 1
    assert cost == 1
    # Verify cover
    assert any(v in soln for v in hyprgraph.ugraph["N1"])


def test_rand_hyper_vertex_cover_triple() -> None:
    """Single net with 3 vertices."""
    hyprgraph = MockHyprgraph(["N1"], {"N1": [0, 1, 2]})
    weight = {0: 1, 1: 1, 2: 1}
    soln, cost = rand_hyper_vertex_cover(hyprgraph, weight, seed=1)
    assert len(soln) == 1
    assert cost == 1
    # Verify cover
    assert any(v in soln for v in hyprgraph.ugraph["N1"])


def test_rand_hyper_vertex_cover_two_nets() -> None:
    """Two nets sharing a vertex."""
    hyprgraph = MockHyprgraph(["N1", "N2"], {"N1": [0, 1], "N2": [1, 2]})
    weight = {0: 1, 1: 1, 2: 1}
    soln, cost = rand_hyper_vertex_cover(hyprgraph, weight, seed=42)
    # Either both nets covered by vertex 1 alone, or by two vertices
    assert cost >= 1
    assert cost <= 2
    # Verify all nets are covered
    for net in hyprgraph.nets:
        assert any(v in soln for v in hyprgraph.ugraph[net])


def test_rand_hyper_vertex_cover_weighted() -> None:
    """Weighted vertices: lighter vertex should be preferred statistically."""
    hyprgraph = MockHyprgraph(["N1"], {"N1": [0, 1]})
    weight = {0: 100, 1: 1}
    picks_heavy = 0
    trials = 200
    for seed in range(trials):
        soln, _ = rand_hyper_vertex_cover(hyprgraph, weight, seed=seed)
        if 0 in soln:
            picks_heavy += 1
    # Vertex 1 (weight 1) should be picked far more often
    assert (
        picks_heavy < trials * 0.1
    ), f"Heavy vertex picked {picks_heavy}/{trials} times"


def test_rand_hyper_vertex_cover_empty() -> None:
    """Empty hypergraph should return empty cover."""
    hyprgraph = MockHyprgraph([], {})
    weight: dict[int, int] = {}
    soln, cost = rand_hyper_vertex_cover(hyprgraph, weight, seed=0)
    assert len(soln) == 0
    assert cost == 0


def test_rand_hyper_vertex_cover_deterministic() -> None:
    """Same seed should produce same result."""
    hyprgraph = MockHyprgraph(["N1", "N2"], {"N1": [0, 1, 2], "N2": [2, 3]})
    weight = {0: 2, 1: 3, 2: 1, 3: 4}
    soln1, cost1 = rand_hyper_vertex_cover(hyprgraph, weight, seed=123)
    soln2, cost2 = rand_hyper_vertex_cover(hyprgraph, weight, seed=123)
    assert soln1 == soln2
    assert cost1 == cost2


def test_rand_hyper_vertex_cover_with_initial_coverset() -> None:
    """Pre-seeded vertex is preserved in the cover."""
    hyprgraph = MockHyprgraph(["N1", "N2"], {"N1": [0, 1], "N2": [1, 2]})
    weight = {0: 1, 1: 1, 2: 1}
    soln, cost = rand_hyper_vertex_cover(hyprgraph, weight, coverset={0}, seed=42)
    assert 0 in soln
    # Verify all nets are covered
    for net in hyprgraph.nets:
        assert any(v in soln for v in hyprgraph.ugraph[net])


def test_rand_hyper_vertex_cover_drawf(drawf_graph: Any) -> None:
    """Test on the drawf netlist fixture (hypergraph with 6 nets)."""
    weight = {node: 1 for node in drawf_graph.ugraph}
    soln, cost = rand_hyper_vertex_cover(drawf_graph, weight, seed=42)
    # Verify all nets are covered
    for net in drawf_graph.nets:
        assert any(v in soln for v in drawf_graph.ugraph[net]), f"Net {net} uncovered"
    assert cost <= len(drawf_graph.ugraph)
    assert cost >= 1
