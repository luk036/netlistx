"""Targeted tests to cover uncovered lines in cover.py.

Missing lines: [250, 251]
Missing branches: [[221, 224], [249, 250]]
"""

from collections import deque

import networkx as nx

from netlistx.cover import (
    _construct_cycle,
    min_cycle_cover,
    min_hyper_vertex_cover,
    min_odd_cycle_cover,
    min_vertex_cover,
)


class TestConstructCycleIfBranch:
    """Cover lines 250-251 in _construct_cycle (depth_now < depth_child)."""

    def test_direct_call_if_branch(self) -> None:
        """Directly call _construct_cycle with depth_now < depth_child to cover the if branch."""
        info = {0: (0, 5), 1: (0, 4), 2: (1, 3), 3: (1, 2)}
        # parent=2: depth_now=3; child=0: depth_child=5 → 3 < 5 → if branch
        result = _construct_cycle(info, 2, 0)
        assert isinstance(result, deque)
        assert len(result) >= 2


class TestMinHyperVertexCoverWithCoverset:
    """Cover branch [221, 224] in min_hyper_vertex_cover (coverset provided)."""

    def test_with_non_none_coverset(self) -> None:
        """Provide a pre-existing coverset to trigger the else branch (coverset is not None)."""

        class MockHyprgraph:
            def __init__(self, nets: list, ugraph: dict) -> None:
                self.nets = nets
                self.ugraph = ugraph

        hyprgraph = MockHyprgraph(["N1", "N2"], {"N1": [0, 1], "N2": [1, 2]})
        weight = {0: 1, 1: 1, 2: 1}
        # Pass a non-None coverset to trigger the [221, 224] branch
        coverset: set = {0}
        result, cost = min_hyper_vertex_cover(hyprgraph, weight, coverset=coverset)
        # The pre-existing vertex should be in the result
        assert 0 in result
        # All nets should be covered
        for net in hyprgraph.nets:
            assert any(v in result for v in hyprgraph.ugraph[net])


class TestCycleCoverBfsDepthCondition:
    """Trigger the depth_now < depth_child condition in _construct_cycle via min_cycle_cover."""

    def test_cycle_cover_with_shortcut_creates_depth_condition(self) -> None:
        """Create a graph where a deeper node has a back edge to a shallower node.

        Graph: 0-1-2-3-4 (path) plus 4-0 (chord from deep node back to source).
        BFS from source 0 discovers 4 via the chord, but after the first cycle cover
        is found and its vertex is added to the cover, subsequent BFS runs may
        discover the back edge from deeper nodes to shallower ones.
        """
        ugraph = nx.Graph()
        # Path 0-1-2-3-4 with chord 4-0 creates a cycle 0-1-2-3-4-0
        ugraph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)])
        weight = {i: 1 for i in range(5)}
        soln, cost = min_cycle_cover(ugraph, weight)
        # Verify it's a valid cycle cover
        remaining = [n for n in ugraph.nodes() if n not in soln]
        subg = ugraph.subgraph(remaining)
        # Should have no cycles (or fewer edges than nodes)
        assert subg.number_of_edges() <= max(0, len(remaining) - 1)
        assert cost >= 0
        assert cost <= sum(weight.values())


class TestGenericBfsCycleEdgeCases:
    """Test edge cases in _generic_bfs_cycle."""

    def test_disconnected_components(self) -> None:
        """Graph with multiple components to exercise different BFS sources."""
        ugraph = nx.Graph()
        # Two triangles (0-1-2-0) and (3-4-5-3)
        ugraph.add_edges_from([(0, 1), (1, 2), (2, 0)])
        ugraph.add_edges_from([(3, 4), (4, 5), (5, 3)])
        weight = {i: 1 for i in range(6)}
        soln, cost = min_cycle_cover(ugraph, weight)
        # Each triangle needs at least one vertex
        assert len(soln) >= 2
        assert cost >= 2


class TestMinVertexCoverEdgeCases:
    """Additional edge cases for min_vertex_cover."""

    def test_with_preexisting_coverset(self) -> None:
        """min_vertex_cover with a pre-existing coverset to cover the else path."""
        ugraph = nx.Graph()
        ugraph.add_edges_from([(0, 1), (1, 2)])
        weight = {0: 1, 1: 1, 2: 1}
        # Pass a non-None coverset
        coverset = {0}
        result, cost = min_vertex_cover(ugraph, weight, coverset=coverset)
        assert 0 in result
        for u, v in ugraph.edges():
            assert u in result or v in result


class TestMinOddCycleCoverEdgeCases:
    """Additional edge cases for min_odd_cycle_cover."""

    def test_with_preexisting_coverset(self) -> None:
        """min_odd_cycle_cover with a pre-existing coverset."""
        ugraph = nx.Graph()
        ugraph.add_edges_from([(0, 1), (1, 2), (2, 0)])
        weight = {0: 1, 1: 1, 2: 1}
        coverset = {0}
        result, cost = min_odd_cycle_cover(ugraph, weight, coverset=coverset)
        assert 0 in result


class TestMinCycleCoverWithPreexistingCoverset:
    """min_cycle_cover with a pre-existing coverset."""

    def test_with_preexisting_coverset(self) -> None:
        ugraph = nx.Graph()
        ugraph.add_edges_from([(0, 1), (1, 2), (2, 0)])
        weight = {0: 1, 1: 1, 2: 1}
        coverset = {0}
        result, cost = min_cycle_cover(ugraph, weight, coverset=coverset)
        assert 0 in result
