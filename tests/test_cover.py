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
