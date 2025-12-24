import pytest
import networkx as nx
from netlistx.cover_ai import min_vertex_cover, min_cycle_cover, min_odd_cycle_cover


class TestCoverAlgorithms:
    @pytest.fixture
    def triangle_graph(self):
        """A simple 3-node cycle."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])
        weight = {0: 1, 1: 1, 2: 1}
        return G, weight

    @pytest.fixture
    def tree_graph(self):
        """A graph with no cycles (should return empty cycle covers)."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])
        weight = {i: 1 for i in range(4)}
        return G, weight

    def test_minimal_vertex_cover(self, triangle_graph):
        G, weight = triangle_graph
        soln, cost = min_vertex_cover(G, weight)
        # Any 2 nodes cover all edges in a triangle.
        # Post-processing ensures it doesn't accidentally pick all 3.
        assert len(soln) == 2
        assert cost == 2

    def test_cycle_cover_filtering(self, tree_graph):
        """Tests that _generic_bfs_cycle ignores edges in a tree."""
        G, weight = tree_graph
        soln, cost = min_cycle_cover(G, weight)
        assert len(soln) == 0
        assert cost == 0

    def test_odd_cycle_cover(self):
        """Test detection of odd vs even cycles."""
        G = nx.Graph()
        # Square (even) and Triangle (odd)
        G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])  # Even
        G.add_edges_from([(4, 5), (5, 6), (6, 4)])  # Odd
        weight = {i: 1 for i in range(7)}

        soln, _ = min_odd_cycle_cover(G, weight)
        # Should only pick a vertex from the triangle (nodes 4, 5, or 6)
        assert any(node in soln for node in [4, 5, 6])
        assert not any(node in soln for node in [0, 1, 2, 3])

    def test_post_processing_minimality(self):
        """Explicitly check if the cover is minimal."""
        G = nx.complete_graph(5)
        weight = {i: 1 for i in range(5)}
        soln, _ = min_vertex_cover(G, weight)

        # For a K5, a minimal vertex cover has 4 nodes.
        # Check if removing any node from the solution breaks the cover.
        for node in list(soln):
            test_soln = set(soln)
            test_soln.remove(node)
            # If any edge is not covered, the original was minimal.
            uncovered_edges = [
                e for e in G.edges() if e[0] not in test_soln and e[1] not in test_soln
            ]
            assert len(uncovered_edges) > 0, f"Node {node} was redundant!"
