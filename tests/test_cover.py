from typing import Any

import networkx as nx

from netlistx.cover import (
    min_cycle_cover,
    min_odd_cycle_cover,
    min_vertex_cover,
    pd_cover,
)


def test_pd_cover() -> None:
    def violate_graph() -> Any:
        yield [0, 1]
        yield [0, 2]
        yield [1, 2]

    weight = {0: 1, 1: 2, 2: 3}
    soln: set = set()
    covered, cost = pd_cover(violate_graph, weight, soln)
    assert covered == {0, 1}
    assert cost == 4


def test_min_vertex_cover_simple() -> None:
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (1, 2)])
    weight = {0: 1, 1: 1, 2: 1}
    soln: set = set()
    covered, cost = min_vertex_cover(ugraph, weight, soln)
    for u, v in ugraph.edges():
        assert u in covered or v in covered


def test_min_cycle_cover_simple() -> None:
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (1, 2), (2, 0)])
    weight = {0: 1, 1: 1, 2: 1}
    soln: set = set()
    covered, cost = min_cycle_cover(ugraph, weight, soln)
    assert len(covered) == 1
    assert cost == 1


def test_min_odd_cycle_cover_simple() -> None:
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (1, 2), (2, 0)])
    weight = {0: 1, 1: 1, 2: 1}
    soln: set = set()
    covered, cost = min_odd_cycle_cover(ugraph, weight, soln)
    assert len(covered) == 1
    assert cost == 1


def test_min_odd_cycle_cover_even_cycle() -> None:
    ugraph = nx.Graph()
    ugraph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])
    weight = {0: 1, 1: 1, 2: 1, 3: 1}
    soln: set = set()
    covered, cost = min_odd_cycle_cover(ugraph, weight, soln)
    assert len(covered) == 0
    assert cost == 0


def test_min_cycle_cover_complex() -> None:
    """Test min_cycle_cover with a more complex graph to exercise _construct_cycle."""
    ugraph = nx.Graph()
    # Create a graph with multiple cycles
    ugraph.add_edges_from(
        [
            (0, 1),
            (1, 2),
            (2, 0),  # Triangle
            (2, 3),
            (3, 4),
            (4, 2),  # Another triangle
            (4, 5),
            (5, 6),
            (6, 4),  # Third triangle
            (0, 7),
            (7, 8),
            (8, 1),  # Additional structure
        ]
    )
    weight = {i: i + 1 for i in range(9)}  # Different weights
    soln: set = set()
    covered, cost = min_cycle_cover(ugraph, weight, soln)
    # The result should be a valid cycle cover
    assert isinstance(covered, set)
    assert isinstance(cost, (int, float))
    # Cost should be the sum of weights of selected vertices
    expected_cost = sum(weight[v] for v in covered)
    assert cost == expected_cost


def test_min_odd_cycle_cover_complex() -> None:
    """Test min_odd_cycle_cover with a more complex graph."""
    ugraph = nx.Graph()
    # Create a graph with both odd and even cycles
    ugraph.add_edges_from(
        [
            (0, 1),
            (1, 2),
            (2, 0),  # Odd cycle (triangle)
            (2, 3),
            (3, 4),
            (4, 5),
            (5, 2),  # Even cycle (4 nodes)
            (5, 6),
            (6, 7),
            (7, 5),  # Another odd cycle
        ]
    )
    weight = {i: 1 for i in range(8)}
    soln: set = set()
    covered, cost = min_odd_cycle_cover(ugraph, weight, soln)
    # The result should be a valid odd cycle cover
    assert isinstance(covered, set)
    assert isinstance(cost, (int, float))
    # Cost should be the sum of weights of selected vertices
    expected_cost = sum(weight[v] for v in covered)
    assert cost == expected_cost
