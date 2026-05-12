"""Tests for the TSP approximation algorithms in netlistx.tsp."""

import math
import random

import networkx as nx

from netlistx.tsp import (
    calculate_total_distance,
    christofides_tsp,
    solve_christofides_2opt_tsp,
    two_opt,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_metric_graph(n: int, seed: int = 42) -> nx.Graph:
    """Build a complete graph with random Euclidean (metric) edge weights."""
    random.seed(seed)
    G = nx.complete_graph(n)
    pos = {i: (random.uniform(0, 100), random.uniform(0, 100)) for i in range(n)}
    for u, v in G.edges():
        dx = pos[u][0] - pos[v][0]
        dy = pos[u][1] - pos[v][1]
        G[u][v]["weight"] = math.sqrt(dx * dx + dy * dy)
    return G


def _is_valid_hamiltonian_cycle(path: list, n: int) -> bool:
    """Check that *path* visits all *n* nodes exactly once and returns."""
    if len(path) != n + 1:
        return False
    if path[0] != path[-1]:
        return False
    visited = path[:-1]
    return len(set(visited)) == n and min(visited) == 0 and max(visited) == n - 1


# ---------------------------------------------------------------------------
# Tests for calculate_total_distance
# ---------------------------------------------------------------------------

class TestCalculateTotalDistance:
    def test_simple_triangle(self) -> None:
        G = nx.complete_graph(3)
        G[0][1]["weight"] = 1.0
        G[1][2]["weight"] = 2.0
        G[0][2]["weight"] = 3.0
        dist = calculate_total_distance([0, 1, 2, 0], G)
        assert dist == 6.0

    def test_zero_weight(self) -> None:
        G = nx.complete_graph(3)
        for u, v in G.edges():
            G[u][v]["weight"] = 0.0
        dist = calculate_total_distance([0, 1, 2, 0], G)
        assert dist == 0.0

    def test_single_edge_return(self) -> None:
        G = nx.Graph()
        G.add_edge(0, 1, weight=5.0)
        dist = calculate_total_distance([0, 1, 0], G)
        assert dist == 10.0


# ---------------------------------------------------------------------------
# Tests for two_opt
# ---------------------------------------------------------------------------

class TestTwoOpt:
    def test_no_improvement_for_optimal_tour(self) -> None:
        """A straight-line tour on collinear points is already optimal."""
        G = nx.complete_graph(4)
        # collinear: 0 - 1 - 2 - 3
        pts = [(0, 0), (1, 0), (2, 0), (3, 0)]
        for u, v in G.edges():
            dx = pts[u][0] - pts[v][0]
            dy = pts[u][1] - pts[v][1]
            G[u][v]["weight"] = math.sqrt(dx * dx + dy * dy)
        tour = [0, 1, 2, 3, 0]
        refined = two_opt(tour, G)
        assert calculate_total_distance(refined, G) == pytest.approx(6.0)

    def test_improves_crossing(self) -> None:
        """A crossing tour should be improved by 2-opt on a convex polygon."""
        G = nx.complete_graph(4)
        # unit square
        pts = [(0, 0), (1, 0), (1, 1), (0, 1)]
        for u, v in G.edges():
            dx = pts[u][0] - pts[v][0]
            dy = pts[u][1] - pts[v][1]
            G[u][v]["weight"] = math.sqrt(dx * dx + dy * dy)
        # A bad crossing tour: 0 → 2 → 1 → 3 → 0
        crossing = [0, 2, 1, 3, 0]
        initial_dist = calculate_total_distance(crossing, G)
        refined = two_opt(crossing, G)
        refined_dist = calculate_total_distance(refined, G)
        assert refined_dist <= initial_dist

    def test_output_is_valid_cycle(self) -> None:
        G = _make_metric_graph(8, seed=1)
        tour = list(range(9))  # some arbitrary cycle
        tour[8] = 0
        refined = two_opt(tour, G)
        assert _is_valid_hamiltonian_cycle(refined, 8)


# ---------------------------------------------------------------------------
# Tests for christofides_tsp
# ---------------------------------------------------------------------------

class TestChristofides:
    def test_small_graph(self) -> None:
        G = _make_metric_graph(5, seed=0)
        tour = christofides_tsp(G)
        assert _is_valid_hamiltonian_cycle(tour, 5)

    def test_medium_graph(self) -> None:
        G = _make_metric_graph(20, seed=1)
        tour = christofides_tsp(G)
        assert _is_valid_hamiltonian_cycle(tour, 20)
        dist = calculate_total_distance(tour, G)
        assert dist > 0

    def test_uniform_weights(self) -> None:
        """With uniform weights every tour has the same cost."""
        G = nx.complete_graph(6)
        for u, v in G.edges():
            G[u][v]["weight"] = 1.0
        tour = christofides_tsp(G)
        assert _is_valid_hamiltonian_cycle(tour, 6)
        assert calculate_total_distance(tour, G) == 6.0

    def test_three_node(self) -> None:
        """Minimum case for Christofides: n=3."""
        G = nx.complete_graph(3)
        G[0][1]["weight"] = 1.0
        G[1][2]["weight"] = 2.0
        G[0][2]["weight"] = 3.0
        tour = christofides_tsp(G)
        assert _is_valid_hamiltonian_cycle(tour, 3)

    def test_tour_includes_all_nodes(self) -> None:
        G = _make_metric_graph(10, seed=7)
        tour = christofides_tsp(G)
        nodes_visited = set(tour[:-1])
        assert nodes_visited == set(range(10))


# ---------------------------------------------------------------------------
# Tests for solve_christofides_2opt_tsp (the combined function)
# ---------------------------------------------------------------------------

class TestSolveChristofides2Opt:
    def test_output_is_valid_cycle(self) -> None:
        G = _make_metric_graph(10, seed=0)
        tour = solve_christofides_2opt_tsp(G)
        assert _is_valid_hamiltonian_cycle(tour, 10)

    def test_improvement_over_baseline(self) -> None:
        """2-opt should never make the tour worse vs Christofides alone."""
        G = _make_metric_graph(15, seed=3)
        christo_tour = christofides_tsp(G)
        combined_tour = solve_christofides_2opt_tsp(G)
        christo_dist = calculate_total_distance(christo_tour, G)
        combined_dist = calculate_total_distance(combined_tour, G)
        assert combined_dist <= christo_dist + 1e-10

    def test_deterministic_repeatability(self) -> None:
        """Same input should produce same output (seeded random)."""
        G = _make_metric_graph(12, seed=5)
        tour1 = solve_christofides_2opt_tsp(G)
        tour2 = solve_christofides_2opt_tsp(G)
        assert tour1 == tour2

    def test_larger_instance(self) -> None:
        """Stress test with n=50 — should complete quickly."""
        G = _make_metric_graph(50, seed=9)
        tour = solve_christofides_2opt_tsp(G)
        assert _is_valid_hamiltonian_cycle(tour, 50)
        dist = calculate_total_distance(tour, G)
        assert dist > 0

    @staticmethod
    def test_approximation_bound_not_violated() -> None:
        """The Christofides part guarantees ≤ 1.5× OPT.
        We can't compute OPT exactly, but we can verify the MST lower bound:
        OPT ≥ MST weight, and our tour should not exceed 1.5× MST.
        """
        G = _make_metric_graph(10, seed=11)
        mst = nx.minimum_spanning_tree(G, weight="weight")
        mst_weight = mst.size(weight="weight")
        tour = solve_christofides_2opt_tsp(G)
        tour_weight = calculate_total_distance(tour, G)
        # Christofides guarantees ≤ 1.5 × OPT, and OPT ≥ MST
        # So tour should be ≤ 1.5 × MST, but 2-opt might make it even better
        assert tour_weight <= 1.5 * mst_weight + 1e-10

    def test_returns_hamiltonian_cycle_structure(self) -> None:
        """Verify the returned path structure: n+1 length, first==last."""
        G = _make_metric_graph(7, seed=2)
        tour = solve_christofides_2opt_tsp(G)
        assert tour[0] == tour[-1]
        assert len(tour) == 8
        assert len(set(tour[:-1])) == 7


# Need pytest.approx for floating comparisons
import pytest  # noqa: E402 (imported here for approx)
