"""
Randomized Approximation Algorithm for Minimum Weighted Vertex Cover (MWVC)

Implements Pitt's randomized algorithm (1985) for solving the minimum weighted
vertex cover problem. The algorithm achieves an expected approximation ratio
of 2.

The algorithm processes each edge in the graph. For each uncovered edge (u, v),
it randomly selects one endpoint to add to the cover, with probability
proportional to the weight of the *other* endpoint:

    P(pick u) = w(v) / (w(u) + w(v))
    P(pick v) = w(u) / (w(u) + w(v))

This biases the selection toward the lighter vertex, which is the key insight
for the weighted case.

Reference:
    L. Pitt, "A Simple Probabilistic Approximation Algorithm for Vertex Cover,"
    Technical Report, Yale University, 1985.
"""

import random
from typing import Any, Callable, MutableMapping, Optional, Set, Tuple, Union

import networkx as nx


def _reverse_delete_cover(
    soln: Set,
    added_order: list,
    is_covered: Callable[[], bool],
) -> None:
    """
    Reverse-delete post-processing: remove redundant vertices from the cover.

    Iterates through algorithm-added vertices in reverse order of addition.
    For each vertex, temporarily removes it and checks if the cover remains valid.
    If the cover is still valid, the vertex is redundant and stays removed.
    Otherwise, it is restored.

    :param soln: The current vertex cover (modified in place).
    :param added_order: List of vertices added by the algorithm (in addition order).
    :param is_covered: A callable that returns True if the current soln is a valid cover.
    """
    for vtx in reversed(added_order):
        soln.remove(vtx)
        if not is_covered():
            soln.add(vtx)


def rand_vertex_cover(
    ugraph: nx.Graph,
    weight: MutableMapping,
    coverset: Optional[Set] = None,
    seed: Optional[int] = None,
) -> Tuple[Set, Union[int, float]]:
    r"""
    Find a minimum weighted vertex cover using Pitt's randomized algorithm.

    This is a randomized 2-approximation algorithm for the minimum weighted
    vertex cover problem. For each uncovered edge, it selects an endpoint to
    add to the cover with probability inversely proportional to its weight.

    :param ugraph: The input undirected graph.
    :type ugraph: nx.Graph
    :param weight: A mapping from vertices to their weights.
    :type weight: MutableMapping
    :param coverset: Optional initial vertex cover (default: empty set).
    :type coverset: Optional[Set]
    :param seed: Random seed for reproducible results (default: None).
    :type seed: Optional[int]

    :return: A tuple of (vertex cover set, total weight).
    :rtype: Tuple[Set, Union[int, float]]

    Examples:
        >>> ugraph = nx.Graph()
        >>> ugraph.add_edges_from([(0, 1), (0, 2), (1, 2)])
        >>> weight = {0: 1, 1: 2, 2: 3}
        >>> soln, cost = rand_vertex_cover(ugraph, weight, seed=42)
        >>> isinstance(soln, set)
        True
        >>> isinstance(cost, (int, float))
        True
        >>> # Verify it's a valid vertex cover
        >>> all(u in soln or v in soln for u, v in ugraph.edges())
        True
    """
    if coverset is None:
        soln: Set = set()
    else:
        soln = set(coverset)

    rng = random.Random(seed)
    added_order: list = []

    for u, v in ugraph.edges():
        if u in soln or v in soln:
            continue
        # Pitt's rule: pick u with prob w(v)/(w(u)+w(v)), else pick v
        w_u = weight[u]
        w_v = weight[v]
        threshold = w_v / (w_u + w_v)
        if rng.random() < threshold:
            soln.add(u)
            added_order.append(u)
        else:
            soln.add(v)
            added_order.append(v)

    # Phase 2: Reverse-Delete Post-Processing
    _reverse_delete_cover(
        soln,
        added_order,
        lambda: all(u in soln or v in soln for u, v in ugraph.edges()),
    )

    total_cost = sum(weight[v] for v in soln)
    return soln, total_cost


def rand_hyper_vertex_cover(
    hyprgraph: Any,
    weight: MutableMapping,
    coverset: Optional[Set] = None,
    seed: Optional[int] = None,
) -> Tuple[Set, Union[int, float]]:
    """
    Find a minimum weighted vertex cover in a hypergraph using Pitt's
    randomized algorithm generalized to hyperedges.

    In a hypergraph, each hyperedge (net) can connect multiple vertices.
    A vertex cover must include at least one vertex from each hyperedge.

    For each uncovered net with vertices {v1, ..., vk}, the algorithm picks
    vertex vi with probability inversely proportional to its weight:

        P(pick vi) = (1/w(vi)) / sum(1/w(vj) for vj in net)

    This is the natural generalization of Pitt's rule: for a standard edge
    (k=2), this reduces to w(v)/(w(u)+w(v)).

    :param hyprgraph: The hypergraph with nets and modules attributes.
    :type hyprgraph: Any
    :param weight: A mapping from vertices to their weights.
    :type weight: MutableMapping
    :param coverset: Optional initial vertex cover (default: empty set).
    :type coverset: Optional[Set]
    :param seed: Random seed for reproducible results (default: None).
    :type seed: Optional[int]

    :return: A tuple of (vertex cover set, total weight).
    :rtype: Tuple[Set, Union[int, float]]

    Examples:
        >>> class MockHyprgraph:
        ...     def __init__(self, nets, ugraph):
        ...         self.nets = nets
        ...         self.ugraph = ugraph
        >>> hyprgraph = MockHyprgraph(["N1", "N2"], {"N1": [0, 1], "N2": [1, 2]})
        >>> weight = {0: 1, 1: 1, 2: 1}
        >>> soln, cost = rand_hyper_vertex_cover(hyprgraph, weight, seed=42)
        >>> isinstance(soln, set)
        True
        >>> isinstance(cost, (int, float))
        True
        >>> # Verify it's a valid cover: each net has at least one endpoint in soln
        >>> all(any(v in soln for v in hyprgraph.ugraph[net]) for net in hyprgraph.nets)
        True
    """
    if coverset is None:
        soln: Set = set()
    else:
        soln = set(coverset)

    rng = random.Random(seed)
    added_order: list = []

    for net in hyprgraph.nets:
        vertices = list(hyprgraph.ugraph[net])
        # Skip nets already covered
        if any(v in soln for v in vertices):
            continue
        if len(vertices) == 0:
            continue
        # Generalized Pitt rule for k vertices:
        # P(pick vi) = (1/w(vi)) / sum(1/w(vj) for vj in net)
        inv_weights = [1.0 / weight[v] for v in vertices]
        total_inv = sum(inv_weights)
        # Normalize to probabilities
        probs = [iw / total_inv for iw in inv_weights]
        # Sample one vertex
        r = rng.random()
        cumulative = 0.0
        for i, p in enumerate(probs):
            cumulative += p
            if r < cumulative:
                vtx = vertices[i]
                soln.add(vtx)
                added_order.append(vtx)
                break

    # Phase 2: Reverse-Delete Post-Processing
    _reverse_delete_cover(
        soln,
        added_order,
        lambda: all(
            any(v in soln for v in hyprgraph.ugraph[net]) for net in hyprgraph.nets
        ),
    )

    total_cost = sum(weight[v] for v in soln)
    return soln, total_cost
