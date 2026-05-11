"""Unit tests for Hadlock's planar MAX-CUT algorithm."""

import networkx as nx
import random

import pytest
from scipy.spatial import Delaunay

from netlistx.hadlock import solve_hadlock_max_cut, validate_max_cut


def _triangle_graph() -> nx.Graph:
    """3-cycle with weights {5, 10, 3}."""
    G = nx.Graph()
    G.add_edge(0, 1, weight=5)
    G.add_edge(1, 2, weight=10)
    G.add_edge(2, 0, weight=3)
    return G


def _square_diag_graph() -> nx.Graph:
    """Square with one diagonal — the standard max-cut test case."""
    G = nx.Graph()
    G.add_edge(1, 2, weight=5)
    G.add_edge(2, 3, weight=10)
    G.add_edge(3, 4, weight=5)
    G.add_edge(4, 1, weight=10)
    G.add_edge(1, 3, weight=2)
    return G


def _grid_graph(rows: int = 2, cols: int = 2) -> nx.Graph:
    """Bipartite grid graph (all edges in the max cut)."""
    G = nx.grid_2d_graph(rows, cols)
    for u, v in G.edges():
        G[u][v]["weight"] = 1
    return G


def _delaunay_graph(n: int = 15, seed: int = 42) -> nx.Graph:
    """Random planar graph via Delaunay triangulation."""
    rng = random.Random(seed)
    pts = [(rng.random(), rng.random()) for _ in range(n)]
    tri = Delaunay(pts)
    G = nx.Graph()
    for s in tri.simplices:
        for i in range(3):
            u, v = sorted((s[i], s[(i + 1) % 3]))
            if not G.has_edge(u, v):
                G.add_edge(u, v, weight=rng.randint(1, 9))
    return G


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


class TestSolveHadlockMaxCut:
    """Tests for :func:`solve_hadlock_max_cut`."""

    def test_triangle(self):
        """A 3-cycle: max cut = 2 edges (total - min weight)."""
        G = _triangle_graph()
        cut = solve_hadlock_max_cut(G)
        ok, val = validate_max_cut(G, cut)
        assert ok
        assert val == 15  # 5 + 10 + 3 - 3 = 15

    def test_square_diagonal(self):
        """Square with diagonal: max cut excludes the diagonal."""
        G = _square_diag_graph()
        cut = solve_hadlock_max_cut(G)
        ok, val = validate_max_cut(G, cut)
        assert ok
        excluded = sum(
            G[u][v].get("weight", 1)
            for u, v in G.edges()
            if tuple(sorted((u, v))) not in cut
        )
        # The lightest odd-cycle-breaking edge is the diagonal (weight 2)
        assert excluded == 2

    def test_grid_bipartite(self):
        """Grid is bipartite → all edges belong to the max cut."""
        G = _grid_graph()
        cut = solve_hadlock_max_cut(G)
        assert len(cut) == G.number_of_edges()
        ok, val = validate_max_cut(G, cut)
        assert ok

    def test_empty_graph(self):
        """Edge-less graph returns empty cut."""
        G = nx.Graph()
        cut = solve_hadlock_max_cut(G)
        assert cut == set()

    def test_single_edge(self):
        """Single edge planar graph."""
        G = nx.Graph()
        G.add_edge(0, 1, weight=7)
        cut = solve_hadlock_max_cut(G)
        ok, val = validate_max_cut(G, cut)
        assert ok
        assert val == 7

    def test_delaunay(self):
        """Triangulated planar graph from Delaunay triangulation."""
        G = _delaunay_graph(15)
        cut = solve_hadlock_max_cut(G)
        ok, val = validate_max_cut(G, cut)
        assert ok
        # At least some edges should be cut
        assert len(cut) > 0

    def test_non_planar_raises(self):
        """K5 is non-planar → must raise."""
        with pytest.raises(nx.NetworkXException):
            solve_hadlock_max_cut(nx.complete_graph(5))

    def test_k3_3_raises(self):
        """K3,3 is non-planar → must raise."""
        with pytest.raises(nx.NetworkXException):
            solve_hadlock_max_cut(nx.complete_bipartite_graph(3, 3))

    def test_default_weight_one(self):
        """Edges without a weight attribute default to 1."""
        G = nx.Graph()
        G.add_edge(0, 1)
        G.add_edge(1, 2)
        G.add_edge(2, 0)
        cut = solve_hadlock_max_cut(G)
        ok, val = validate_max_cut(G, cut)
        assert ok
        assert val == 2  # 3 total, min = 1, cut = 2

    def test_larger_delaunay(self):
        """Larger random instance for stress."""
        G = _delaunay_graph(50, seed=123)
        cut = solve_hadlock_max_cut(G)
        ok, _ = validate_max_cut(G, cut)
        assert ok


class TestValidateMaxCut:
    """Tests for :func:`validate_max_cut`."""

    def test_valid_cut(self):
        """A correct cut should validate as bipartite."""
        G = _square_diag_graph()
        cut = {(1, 2), (2, 3), (3, 4), (4, 1)}
        ok, val = validate_max_cut(G, cut)
        assert ok
        assert val == 30

    def test_invalid_cut(self):
        """A cut containing a triangle is *not* bipartite."""
        G = _triangle_graph()
        # All 3 edges — contains an odd cycle
        cut = {(0, 1), (1, 2), (2, 0)}
        ok, val = validate_max_cut(G, cut)
        assert not ok

    def test_cut_weight_no_attribute(self):
        """Weight defaults to 1 when the attribute is missing."""
        G = nx.Graph()
        G.add_edge(0, 1)
        G.add_edge(1, 2)
        ok, val = validate_max_cut(G, {(0, 1)})
        assert ok
        assert val == 1
