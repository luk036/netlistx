"""Targeted tests to cover uncovered lines in netlist_algo.py.

Missing lines: [185, 186, 193, 194, 195, 198]
Missing branches: [[184, 185], [191, 193], [194, 172], [194, 195], [195, 194], [195, 198]]
"""

from netlistx.netlist_algo import min_maximal_matching


class MockUgraph:
    """Mock graph for testing min_maximal_matching."""

    def __init__(self, net_to_modules, module_to_nets):
        self.net_to_modules = net_to_modules
        self.module_to_nets = module_to_nets

    def __getitem__(self, key):
        if key in self.net_to_modules:
            return self.net_to_modules[key]
        return self.module_to_nets[key]


class MockHyprgraph:
    """Mock hypergraph for testing."""

    def __init__(self, nets, ugraph):
        self.nets = nets
        self.ugraph = ugraph


class TestMinMaximalMatchingUnequalWeights:
    """Cover lines 184-186 and 193-198 in min_maximal_matching.

    These lines handle the case where a neighboring net has a lower gap than
    the current net, causing min_net != net and subsequent gap updates.
    """

    def test_unequal_weights_triggers_alternative_selection(self) -> None:
        """Use nets with unequal weights so min_net != net triggers.

        With weights [1, 5, 1], the middle heavy net should be skipped
        in favor of lighter neighbors.
        """
        ugraph = MockUgraph(
            {
                "N1": [0, 1],
                "N2": [1, 2],
                "N3": [2, 3],
            },
            {
                0: ["N1"],
                1: ["N1", "N2"],
                2: ["N2", "N3"],
                3: ["N3"],
            },
        )
        hyprgraph = MockHyprgraph(["N1", "N2", "N3"], ugraph)
        weight = {"N1": 1, "N2": 5, "N3": 1}
        matchset, cost = min_maximal_matching(hyprgraph, weight)  # type: ignore[arg-type]
        assert isinstance(matchset, set)
        # N2 is heavy, so it should NOT be in the matching
        assert "N2" not in matchset
        # Total cost should be low (N1 + N3)
        assert cost == 2

    def test_different_weights_chain(self) -> None:
        """Chain of nets with descending weights to exercise gap updates.

        With weights [3, 2, 1], processing N1 should trigger the inner loop
        to find N3 as the min-gap net.
        """
        ugraph = MockUgraph(
            {
                "N1": [0, 1],
                "N2": [1, 2],
                "N3": [2, 3],
            },
            {
                0: ["N1"],
                1: ["N1", "N2"],
                2: ["N2", "N3"],
                3: ["N3"],
            },
        )
        hyprgraph = MockHyprgraph(["N1", "N2", "N3"], ugraph)
        weight = {"N1": 3, "N2": 2, "N3": 1}
        matchset, cost = min_maximal_matching(hyprgraph, weight)  # type: ignore[arg-type]
        assert isinstance(matchset, set)
        # With descending weights, the algorithm should pick lighter nets
        assert cost <= 3

    def test_scattered_star_graph(self) -> None:
        """Star-like hypergraph where center module connects multiple nets.

        This tests the case when min_net != net (line 191) and gap updates
        (lines 193-198) are exercised.
        """
        ugraph = MockUgraph(
            {
                "N1": [0, 1],
                "N2": [0, 2],
                "N3": [0, 3],
                "N4": [0, 4],
            },
            {
                0: ["N1", "N2", "N3", "N4"],
                1: ["N1"],
                2: ["N2"],
                3: ["N3"],
                4: ["N4"],
            },
        )
        hyprgraph = MockHyprgraph(["N1", "N2", "N3", "N4"], ugraph)
        weight = {"N1": 10, "N2": 1, "N3": 10, "N4": 10}
        matchset, cost = min_maximal_matching(hyprgraph, weight)  # type: ignore[arg-type]
        assert isinstance(matchset, set)
        # N2 (weight 1) should be selected, others should depend on iteration order
        assert "N2" in matchset
        assert cost >= 1
        # Only non-overlapping nets can be selected (they all share module 0)
        # So only one net can be in the matching
        assert len(matchset) == 1
