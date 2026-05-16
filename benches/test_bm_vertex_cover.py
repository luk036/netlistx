from typing import Any

import networkx as nx

from netlistx.cover import min_hyper_vertex_cover, min_vertex_cover
from netlistx.netlist import create_random_hgraph
from netlistx.rand_cover import rand_hyper_vertex_cover, rand_vertex_cover

_SEED = 12345


def _make_graph(n, p):
    ugraph = nx.fast_gnp_random_graph(n, p, seed=42)
    rng = __import__("random").Random(_SEED)
    weight = {v: rng.randint(1, 10) for v in ugraph.nodes()}
    return ugraph, weight


def _make_graph_m(n, m):
    p = min(1.0, (2.0 * m) / (n * (n - 1)))
    return _make_graph(n, p)


GRAPHS: list[tuple[nx.Graph, dict[int, int]]] = []
for n, m in [(50, 150), (200, 800), (500, 2500), (1000, 5000)]:
    g, w = _make_graph_m(n, m)
    GRAPHS.append((g, w))


def _check(ugraph, weight, soln, cost):
    assert all(u in soln or v in soln for u, v in ugraph.edges())
    assert cost == sum(weight[v] for v in soln)


def _run_vc(ugraph, weight):
    soln, cost = min_vertex_cover(ugraph, weight)
    return soln, cost


def _run_rand_vc(ugraph, weight):
    soln, cost = rand_vertex_cover(ugraph, weight, seed=0)
    return soln, cost


# ---- hypergraph helpers ---------------------------------------------------

HGRAPHS: list[tuple[Any, dict[int, int]]] = []
rng = __import__("random").Random(_SEED)
for n, m, eta in [(50, 30, 0.15), (200, 120, 0.1), (500, 300, 0.08), (1000, 500, 0.05)]:
    h = create_random_hgraph(n, m, eta)
    w = {v: rng.randint(1, 10) for v in range(n)}
    HGRAPHS.append((h, w))


def _check_h(hyprgraph, weight, soln, cost):
    for net in hyprgraph.nets:
        assert any(v in soln for v in hyprgraph.ugraph[net]), f"net {net} uncovered"
    assert cost == sum(weight[v] for v in soln if v in weight)


def _run_hvc(hyprgraph, weight):
    soln, cost = min_hyper_vertex_cover(hyprgraph, weight)
    return soln, cost


def _run_rand_hvc(hyprgraph, weight):
    soln, cost = rand_hyper_vertex_cover(hyprgraph, weight, seed=0)
    return soln, cost


# ---- graph vertex cover tests ---------------------------------------------


def test_vc_small(benchmark: Any) -> None:
    ugraph, weight = GRAPHS[0]
    soln, cost = benchmark(_run_vc, ugraph, weight)
    _check(ugraph, weight, soln, cost)


def test_vc_medium(benchmark: Any) -> None:
    ugraph, weight = GRAPHS[1]
    soln, cost = benchmark(_run_vc, ugraph, weight)
    _check(ugraph, weight, soln, cost)


def test_vc_large(benchmark: Any) -> None:
    ugraph, weight = GRAPHS[2]
    soln, cost = benchmark(_run_vc, ugraph, weight)
    _check(ugraph, weight, soln, cost)


def test_vc_xlarge(benchmark: Any) -> None:
    ugraph, weight = GRAPHS[3]
    soln, cost = benchmark(_run_vc, ugraph, weight)
    _check(ugraph, weight, soln, cost)


def test_rand_vc_small(benchmark: Any) -> None:
    ugraph, weight = GRAPHS[0]
    soln, cost = benchmark(_run_rand_vc, ugraph, weight)
    _check(ugraph, weight, soln, cost)


def test_rand_vc_medium(benchmark: Any) -> None:
    ugraph, weight = GRAPHS[1]
    soln, cost = benchmark(_run_rand_vc, ugraph, weight)
    _check(ugraph, weight, soln, cost)


def test_rand_vc_large(benchmark: Any) -> None:
    ugraph, weight = GRAPHS[2]
    soln, cost = benchmark(_run_rand_vc, ugraph, weight)
    _check(ugraph, weight, soln, cost)


def test_rand_vc_xlarge(benchmark: Any) -> None:
    ugraph, weight = GRAPHS[3]
    soln, cost = benchmark(_run_rand_vc, ugraph, weight)
    _check(ugraph, weight, soln, cost)


# ---- hypergraph vertex cover tests ----------------------------------------


def test_hvc_small(benchmark: Any) -> None:
    hyprgraph, weight = HGRAPHS[0]
    soln, cost = benchmark(_run_hvc, hyprgraph, weight)
    _check_h(hyprgraph, weight, soln, cost)


def test_hvc_medium(benchmark: Any) -> None:
    hyprgraph, weight = HGRAPHS[1]
    soln, cost = benchmark(_run_hvc, hyprgraph, weight)
    _check_h(hyprgraph, weight, soln, cost)


def test_hvc_large(benchmark: Any) -> None:
    hyprgraph, weight = HGRAPHS[2]
    soln, cost = benchmark(_run_hvc, hyprgraph, weight)
    _check_h(hyprgraph, weight, soln, cost)


def test_hvc_xlarge(benchmark: Any) -> None:
    hyprgraph, weight = HGRAPHS[3]
    soln, cost = benchmark(_run_hvc, hyprgraph, weight)
    _check_h(hyprgraph, weight, soln, cost)


def test_rand_hvc_small(benchmark: Any) -> None:
    hyprgraph, weight = HGRAPHS[0]
    soln, cost = benchmark(_run_rand_hvc, hyprgraph, weight)
    _check_h(hyprgraph, weight, soln, cost)


def test_rand_hvc_medium(benchmark: Any) -> None:
    hyprgraph, weight = HGRAPHS[1]
    soln, cost = benchmark(_run_rand_hvc, hyprgraph, weight)
    _check_h(hyprgraph, weight, soln, cost)


def test_rand_hvc_large(benchmark: Any) -> None:
    hyprgraph, weight = HGRAPHS[2]
    soln, cost = benchmark(_run_rand_hvc, hyprgraph, weight)
    _check_h(hyprgraph, weight, soln, cost)


def test_rand_hvc_xlarge(benchmark: Any) -> None:
    hyprgraph, weight = HGRAPHS[3]
    soln, cost = benchmark(_run_rand_hvc, hyprgraph, weight)
    _check_h(hyprgraph, weight, soln, cost)
