from typing import Any

import networkx as nx

from netlistx.cover import min_odd_cycle_cover

_SEED = 12345


def _make_graph_m(n, m):
    p = min(1.0, (2.0 * m) / (n * (n - 1)))
    ugraph = nx.fast_gnp_random_graph(n, p, seed=42)
    rng = __import__("random").Random(_SEED)
    weight = {v: rng.randint(1, 10) for v in ugraph.nodes()}
    return ugraph, weight


GRAPHS: list[tuple[nx.Graph, dict[int, int]]] = []
for n, m in [(50, 75), (100, 150), (200, 300), (400, 600)]:
    g, w = _make_graph_m(n, m)
    GRAPHS.append((g, w))


def _check(ugraph, weight, soln, cost):
    remaining = ugraph.subgraph([v for v in ugraph.nodes() if v not in soln])
    for cycle in nx.cycle_basis(remaining):
        assert len(cycle) % 2 == 0, f"odd cycle remains after cover: {cycle}"
    assert cost == sum(weight[v] for v in soln)


def _run(ugraph, weight):
    return min_odd_cycle_cover(ugraph, weight)


def test_odd_cycle_cover_small(benchmark: Any) -> None:
    ugraph, weight = GRAPHS[0]
    soln, cost = benchmark(_run, ugraph, weight)
    _check(ugraph, weight, soln, cost)


def test_odd_cycle_cover_medium(benchmark: Any) -> None:
    ugraph, weight = GRAPHS[1]
    soln, cost = benchmark(_run, ugraph, weight)
    _check(ugraph, weight, soln, cost)


def test_odd_cycle_cover_large(benchmark: Any) -> None:
    ugraph, weight = GRAPHS[2]
    soln, cost = benchmark(_run, ugraph, weight)
    _check(ugraph, weight, soln, cost)


def test_odd_cycle_cover_xlarge(benchmark: Any) -> None:
    ugraph, weight = GRAPHS[3]
    soln, cost = benchmark(_run, ugraph, weight)
    _check(ugraph, weight, soln, cost)
