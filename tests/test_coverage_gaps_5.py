"""Targeted tests for tsp.py, skeleton.py, and rand_cover.py.

tsp.py missing lines: [64, 89, 90, 91]  (make_l2_graph)
skeleton.py missing lines: [139]  (run())
rand_cover.py missing lines: [186]  (empty net branch)
"""

import networkx as nx

from netlistx.rand_cover import rand_hyper_vertex_cover
from netlistx.skeleton import run
from netlistx.tsp import make_l2_graph


class TestMakeL2Graph:
    """Cover lines 89-91 and line 64 in tsp.py (make_l2_graph)."""

    def test_make_l2_graph_basic(self) -> None:
        """Directly test make_l2_graph to cover its body."""
        G, pos = make_l2_graph(5, seed=42)
        assert len(G.nodes()) == 5
        assert G.number_of_edges() == 10
        assert G[0][1]["weight"] > 0
        # Verify Euclidean distance: sqrt((x0-x1)^2 + (y0-y1)^2)
        dx = pos[0][0] - pos[1][0]
        dy = pos[0][1] - pos[1][1]
        expected = (dx * dx + dy * dy) ** 0.5
        assert G[0][1]["weight"] == expected

    def test_make_l2_graph_different_seed(self) -> None:
        """Test make_l2_graph with a different seed."""
        G1, _ = make_l2_graph(5, seed=0)
        G2, _ = make_l2_graph(5, seed=1)
        # Different seeds should give different distances
        w1 = G1[0][1]["weight"]
        w2 = G2[0][1]["weight"]
        # Very unlikely to be exactly equal
        assert w1 != w2

    def test_make_l2_graph_large_instance(self) -> None:
        """Test make_l2_graph with a larger graph."""
        G, _ = make_l2_graph(20, seed=7)
        assert len(G.nodes()) == 20
        assert G.number_of_edges() == 190  # n*(n-1)/2


class TestSkeletonRun:
    """Cover line 139 in skeleton.py (run())."""

    def test_run_calls_main(self, monkeypatch) -> None:
        """Test that run() calls main with sys.argv[1:]."""
        import sys
        monkeypatch.setattr(sys, "argv", ["skeleton", "7"])
        # Should not raise
        run()


class TestRandCoverEmptyNet:
    """Cover line 186 in rand_cover.py (empty net in hypergraph)."""

    def test_hyper_vertex_cover_empty_net(self) -> None:
        """Hypergraph with an empty net should trigger the continue at line 186."""
        class MockHyprgraph:
            def __init__(self, nets, ugraph):
                self.nets = nets
                self.ugraph = ugraph

        # Net "N2" is empty (no vertices)
        hyprgraph = MockHyprgraph(
            ["N1", "N2"], {"N1": [0, 1], "N2": []}
        )
        weight = {0: 1, 1: 1}
        soln, cost = rand_hyper_vertex_cover(hyprgraph, weight, seed=42)
        # Empty net doesn't need covering, so only N1 needs coverage
        assert isinstance(soln, set)
        assert isinstance(cost, (int, float))
        # At least one vertex from N1 should be in the cover
        assert any(v in soln for v in [0, 1])
