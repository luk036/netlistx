from typing import Any

import networkx as nx
import pytest
from numba import cuda  # type: ignore[import-untyped]

from netlistx.rand_cover_gpu import rand_vertex_cover_gpu

pytestmark = pytest.mark.skipif(not cuda.is_available(), reason="No CUDA GPU available")


def test_gpu_vertex_cover_simple() -> None:
    """Triangle with unit weights."""
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (0, 2), (1, 2)])
    weight = {0: 1, 1: 1, 2: 1}
    soln, cost = rand_vertex_cover_gpu(ugraph, weight, num_trials=64, seed=0)
    # Any 2 vertices cover a triangle
    assert len(soln) == 2
    assert cost == 2
    for u, v in ugraph.edges():
        assert u in soln or v in soln


def test_gpu_vertex_cover_line() -> None:
    """Line graph (3 nodes, 2 edges)."""
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (1, 2)])
    weight = {0: 1, 1: 1, 2: 1}
    soln, cost = rand_vertex_cover_gpu(ugraph, weight, num_trials=64, seed=1)
    assert 1 <= cost <= 2
    for u, v in ugraph.edges():
        assert u in soln or v in soln


def test_gpu_vertex_cover_star() -> None:
    """Star graph: center covers all edges."""
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (0, 2), (0, 3)])
    weight = {0: 1, 1: 1, 2: 1, 3: 1}
    soln, cost = rand_vertex_cover_gpu(ugraph, weight, num_trials=256, seed=2)
    # The GPU runs many trials and picks best — likely finds center-only cover
    assert 1 <= cost <= 3
    for u, v in ugraph.edges():
        assert u in soln or v in soln


def test_gpu_vertex_cover_weighted() -> None:
    """Weighted edge: lighter vertex should be picked more often."""
    ugraph = nx.Graph()
    ugraph.add_edge(0, 1)
    weight = {0: 100, 1: 1}
    soln, cost = rand_vertex_cover_gpu(ugraph, weight, num_trials=512, seed=42)
    assert len(soln) == 1
    # The lighter vertex (1) should be selected almost always across trials
    assert 1 in soln
    assert cost == 1


def test_gpu_vertex_cover_empty_graph() -> None:
    """Empty graph returns empty cover."""
    ugraph = nx.Graph()
    weight: dict[int, int] = {}
    soln, cost = rand_vertex_cover_gpu(ugraph, weight, num_trials=64, seed=0)
    assert len(soln) == 0
    assert cost == 0


def test_gpu_vertex_cover_single_edge() -> None:
    """Single edge with equal weights."""
    ugraph = nx.Graph()
    ugraph.add_edge(0, 1)
    weight = {0: 1, 1: 1}
    soln, cost = rand_vertex_cover_gpu(ugraph, weight, num_trials=64, seed=7)
    assert len(soln) == 1
    assert cost == 1
    for u, v in ugraph.edges():
        assert u in soln or v in soln


def test_gpu_vertex_cover_deterministic_seed() -> None:
    """Same seed produces same result across runs."""
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])
    weight = {0: 2, 1: 3, 2: 1, 3: 4}
    soln1, cost1 = rand_vertex_cover_gpu(ugraph, weight, num_trials=128, seed=123)
    soln2, cost2 = rand_vertex_cover_gpu(ugraph, weight, num_trials=128, seed=123)
    assert soln1 == soln2
    assert cost1 == cost2


def test_gpu_vertex_cover_with_initial_coverset() -> None:
    """Pre-seeded vertex is preserved in the cover."""
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (1, 2), (2, 0)])
    weight = {0: 1, 1: 1, 2: 1}
    soln, cost = rand_vertex_cover_gpu(
        ugraph, weight, coverset={0}, num_trials=64, seed=42
    )
    assert 0 in soln
    for u, v in ugraph.edges():
        assert u in soln or v in soln


def test_gpu_vertex_cover_drawf(drawf_graph: Any) -> None:
    """Integration with the drawf graph fixture."""
    weight = {node: 1 for node in drawf_graph.ugraph}
    soln, cost = rand_vertex_cover_gpu(
        drawf_graph.ugraph, weight, num_trials=256, seed=42
    )
    for u, v in drawf_graph.ugraph.edges():
        assert u in soln or v in soln
    assert cost <= len(drawf_graph.ugraph)
    assert cost >= 1


def test_gpu_larger_graph() -> None:
    """Random graph with 50 nodes, 200 edges."""
    ugraph = nx.gnm_random_graph(50, 200, seed=0)
    weight = {node: 1 for node in ugraph}
    soln, cost = rand_vertex_cover_gpu(ugraph, weight, num_trials=256, seed=1)
    for u, v in ugraph.edges():
        assert u in soln or v in soln
    # Vertex cover can't be larger than all vertices
    assert cost <= 50
    # A graph with 200 edges must have a cover of at least some size
    assert cost >= 1
