"""Targeted tests to cover uncovered lines in hadlock.py.

Missing lines: [109, 180, 195, 196, 197]
Missing branches: [[108, 109], [179, 180], [192, 195], [196, 197], [196, 200], [209, 207], [223, 221]]
"""

import networkx as nx

from netlistx.hadlock import solve_hadlock_max_cut, validate_max_cut


class TestHadlockBridgeEdge:
    """Cover line 109: bridge/boundary edge in _build_dual."""

    def test_graph_with_bridge(self) -> None:
        """A planar graph containing a bridge edge.

        Two triangles connected by a single bridge edge.
        The bridge should appear in only one face, triggering the continue at line 109.
        """
        G = nx.Graph()
        # Triangle 1: 0-1-2-0
        G.add_edge(0, 1, weight=2)
        G.add_edge(1, 2, weight=3)
        G.add_edge(2, 0, weight=4)
        # Bridge: 2-3
        G.add_edge(2, 3, weight=1)
        # Triangle 2: 3-4-5-3
        G.add_edge(3, 4, weight=5)
        G.add_edge(4, 5, weight=6)
        G.add_edge(5, 3, weight=7)

        cut = solve_hadlock_max_cut(G)
        ok, val = validate_max_cut(G, cut)
        assert ok
        assert val > 0


class TestHadlockNoFacesComponent:
    """Cover line 180: component with no faces."""

    def test_tiny_component(self) -> None:
        """A single edge component with no faces may trigger _solve_hadlock_component."""
        G = nx.Graph()
        G.add_edge(0, 1, weight=5)

        cut = solve_hadlock_max_cut(G)
        ok, val = validate_max_cut(G, cut)
        assert ok
        assert val == 5


class TestHadlockOddFaceGuard:
    """Cover lines 195-197: guard for odd number of odd faces."""

    def test_single_odd_face_guard(self) -> None:
        """A graph with a single odd face (if handshaking lemma is violated).
        
        This is very hard to trigger in practice since handshaking always holds.
        We test a simple case that works through the normal path.
        """
        G = nx.Graph()
        G.add_edge(0, 1, weight=1)
        G.add_edge(1, 2, weight=1)
        G.add_edge(2, 0, weight=1)

        cut = solve_hadlock_max_cut(G)
        ok, val = validate_max_cut(G, cut)
        assert ok


class TestHadlockBiconnectedComponents:
    """Test hadlock with multiple biconnected components."""

    def test_two_separate_triangles(self) -> None:
        """Two disconnected triangles - multiple components with odd cycles."""
        G = nx.Graph()
        G.add_edge(0, 1, weight=2)
        G.add_edge(1, 2, weight=3)
        G.add_edge(2, 0, weight=4)
        G.add_edge(3, 4, weight=5)
        G.add_edge(4, 5, weight=6)
        G.add_edge(5, 3, weight=7)

        cut = solve_hadlock_max_cut(G)
        ok, val = validate_max_cut(G, cut)
        assert ok
        # Each triangle: max cut = sum - min weight
        # Triangle 1: 2+3+4 - 2 = 7, Triangle 2: 5+6+7 - 5 = 13, total = 20
        assert val == 20

    def test_odd_faces_different_path_weights(self) -> None:
        """Graph with different edge weights to exercise dual shortest paths."""
        G = nx.Graph()
        G.add_edge(0, 1, weight=1)
        G.add_edge(1, 2, weight=100)
        G.add_edge(2, 0, weight=1)
        cut = solve_hadlock_max_cut(G)
        ok, val = validate_max_cut(G, cut)
        assert ok
        # Max cut = sum - min_weight = 102 - 1 = 101
        assert val == 101
