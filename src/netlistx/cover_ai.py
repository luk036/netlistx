"""
Cover Algorithms with Reverse-Delete Post-Processing (cover_ai.py)

This module implements primal-dual approximation algorithms for various covering
problems in graphs, with enhanced post-processing using the reverse-delete technique.

The main purpose is to find minimal sets of vertices that "cover" certain
structures in a graph, such as all edges, cycles, or odd cycles.

The algorithms use a two-phase approach:
1. Primal-Dual Selection: Iteratively builds a solution by selecting elements
   with minimum reduced cost (gap).
2. Reverse-Delete Post-Processing: Removes redundant elements from the solution
   in reverse order of selection to ensure minimality.

Key functions:
- pd_cover: Core primal-dual algorithm with reverse-delete post-processing
- min_vertex_cover: Find minimum weighted vertex cover in a graph
- min_hyper_vertex_cover: Find minimum weighted vertex cover in a hypergraph
- min_cycle_cover: Find minimum weighted set of vertices covering all cycles
- min_odd_cycle_cover: Find minimum weighted set of vertices covering all odd cycles

The algorithms are useful in electronic design automation (EDA) for problems
like logic optimization and circuit analysis.
"""

import copy
from collections import deque
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    Generator,
    MutableMapping,
    Optional,
    Set,
    Tuple,
    Union,
)

import networkx as nx


def pd_cover(
    violate: Callable, weight: MutableMapping, soln: Set
) -> Tuple[Set, Union[int, float]]:
    """
    Primal-dual approximation algorithm with reverse-delete post-processing.

    This is a core algorithm that finds a minimal weighted cover by combining
    primal-dual selection with reverse-delete refinement.

    :param violate: A callable that returns a generator of violating sets.
        Each set contains elements where at least one must be added to the cover.
    :type violate: Callable
    :param weight: A mutable mapping from elements to their weights.
    :type weight: MutableMapping
    :param soln: The initial solution set (may be empty or contain pre-selected elements).
    :type soln: Set

    :return: A tuple containing the minimal cover set and its total weight.
    :rtype: Tuple[Set, Union[int, float]]

    The algorithm maintains a "gap" for each element, representing the remaining
    budget. In each iteration, it selects the element with minimum gap from a
    violating set. After all violations are resolved, it performs reverse-delete
    to remove any redundant elements.
    """
    total_dual_cost = 0
    gap = copy.copy(weight)
    added_order = []

    # Phase 1: Primal-Dual Selection
    for S in violate():
        min_vtx = min(S, key=lambda vertex: gap[vertex])
        min_val = gap[min_vtx]

        if min_vtx not in soln:
            soln.add(min_vtx)
            added_order.append(min_vtx)

        total_dual_cost += min_val
        for vtx in S:
            gap[vtx] -= min_val

    # Phase 2: Post-processing (Reverse-Delete)
    # Removes redundant elements to ensure the cover is minimal.
    for vtx in reversed(added_order):
        soln.remove(vtx)
        is_redundant = True
        # Check if any structure remains uncovered without this vertex
        for _ in violate():
            is_redundant = False
            break

        if not is_redundant:
            soln.add(vtx)

    final_prml_cost = sum(weight[vtx] for vtx in soln)
    assert total_dual_cost <= final_prml_cost
    return soln, final_prml_cost


def min_vertex_cover(
    ugraph: nx.Graph, weight: MutableMapping, coverset: Optional[Set] = None
) -> Tuple[Set, Union[int, float]]:
    """
    Find minimum weighted vertex cover using primal-dual with reverse-delete.

    A vertex cover is a set of vertices where every edge in the graph has
    at least one endpoint in the set.

    :param ugraph: The input undirected graph.
    :type ugraph: nx.Graph
    :param weight: A mapping from vertices to their weights.
    :type weight: MutableMapping
    :param coverset: Optional initial vertex cover (default: empty set).
    :type coverset: Optional[Set]

    :return: A tuple of (minimum vertex cover set, total weight).
    :rtype: Tuple[Set, Union[int, float]]
    """
    if coverset is None:
        coverset = set()

    def violate_graph() -> Generator:
        for utx, vtx in ugraph.edges():
            if utx in coverset or vtx in coverset:
                continue
            yield [utx, vtx]

    return pd_cover(violate_graph, weight, coverset)


def min_hyper_vertex_cover(
    hyprgraph: Any, weight: MutableMapping, coverset: Optional[Set] = None
) -> Tuple[Set, Union[int, float]]:
    """
    Find minimum weighted vertex cover in a hypergraph using primal-dual.

    In a hypergraph, each hyperedge (net) can connect multiple vertices.
    A vertex cover must include at least one vertex from each hyperedge.

    :param hyprgraph: The hypergraph with nets and modules attributes.
    :param weight: A mapping from vertices to their weights.
    :type weight: MutableMapping
    :param coverset: Optional initial vertex cover (default: empty set).
    :type coverset: Optional[Set]

    :return: A tuple of (minimum vertex cover set, total weight).
    :rtype: Tuple[Set, Union[int, float]]
    """
    if coverset is None:
        coverset = set()

    def violate_netlist() -> Generator:
        for net in hyprgraph.nets:
            if any(vtx in coverset for vtx in hyprgraph.ugraph[net]):
                continue
            yield hyprgraph.ugraph[net]

    return pd_cover(violate_netlist, weight, coverset)


def _construct_cycle(
    info: Dict[Any, Tuple[Any, int]], parent: Any, child: Any
) -> Deque[Any]:
    """
    Reconstruct a cycle path from BFS parent-child relationship.

    :param info: Dictionary mapping each node to (parent, depth) tuple.
    :type info: Dict[Any, Tuple[Any, int]]
    :param parent: One endpoint of the detected cycle edge.
    :param child: Other endpoint of the detected cycle edge.

    :return: A deque containing the cycle nodes in order.
    :rtype: Deque[Any]
    """
    _, depth_now = info[parent]
    _, depth_child = info[child]
    if depth_now < depth_child:
        node_a, depth_a = parent, depth_now
        node_b, depth_b = child, depth_child
    else:
        node_a, depth_a = child, depth_child
        node_b, depth_b = parent, depth_now
    S: Deque = deque()
    while depth_a < depth_b:
        S.append(node_a)
        node_a, depth_a = info[node_a]
    while node_a != node_b:
        S.append(node_a)
        S.appendleft(node_b)
        node_a, _ = info[node_a]
        node_b, _ = info[node_b]
    S.appendleft(node_b)
    return S


def _generic_bfs_cycle(
    ugraph: nx.Graph, coverset: Set[Any]
) -> Generator[Tuple[Dict[Any, Tuple[Any, int]], Any, Any], None, None]:
    """
    Find cycles using BFS restricted to cyclable edges.

    This function uses biconnected components and chain (ear) decomposition
    to identify edges that can form cycles, then performs BFS to detect them.

    :param ugraph: The input undirected graph.
    :type ugraph: nx.Graph
    :param coverset: Set of nodes to exclude from cycle detection.
    :type coverset: Set[Any]

    :yields: Tuples of (info, parent, child) where info is the BFS parent/depth
             dictionary, and parent-child is the back edge forming a cycle.
    :rtype: Generator[Tuple[Dict[Any, Tuple[Any, int]], Any, Any], None, None]
    """
    # Identify edges that can actually form cycles
    cyclable_edges = set()
    for component in nx.biconnected_components(ugraph):
        if len(component) >= 3:
            subgraph = ugraph.subgraph(component)
            # Use chain (ear) decomposition to find cycle-forming edges
            for chain in nx.chain_decomposition(subgraph):
                for edge in chain:
                    cyclable_edges.add(tuple(sorted(edge)))

    depth_limit = len(ugraph)
    nodelist = list(ugraph.nodes())
    for source in nodelist:
        if source in coverset:
            continue
        info = {source: (source, depth_limit)}
        queue = deque([source])
        while queue:
            parent = queue.popleft()
            succ, depth_now = info[parent]
            for child in ugraph.neighbors(parent):
                edge = tuple(sorted((parent, child)))
                if child in coverset or edge not in cyclable_edges:
                    continue
                if child not in info:
                    info[child] = (parent, depth_now - 1)
                    queue.append(child)
                    continue
                if succ == child:
                    continue
                yield info, parent, child


def min_cycle_cover(
    ugraph: nx.Graph, weight: MutableMapping, coverset: Optional[Set] = None
) -> Tuple[Set, Union[int, float]]:
    """
    Find minimum weighted set of vertices covering all cycles.

    A cycle cover is a set of vertices such that removing them from the graph
    eliminates all cycles.

    :param ugraph: The input undirected graph.
    :type ugraph: nx.Graph
    :param weight: A mapping from vertices to their weights.
    :type weight: MutableMapping
    :param coverset: Optional initial cycle cover (default: empty set).
    :type coverset: Optional[Set]

    :return: A tuple of (minimum cycle cover set, total weight).
    :rtype: Tuple[Set, Union[int, float]]
    """
    if coverset is None:
        coverset = set()

    def find_cycle() -> Any:
        for info, parent, child in _generic_bfs_cycle(ugraph, coverset):
            return _construct_cycle(info, parent, child)

    def violate() -> Generator:
        while True:
            S = find_cycle()
            if S is None:
                break
            yield S

    return pd_cover(violate, weight, coverset)


def min_odd_cycle_cover(
    ugraph: nx.Graph, weight: MutableMapping, coverset: Optional[Set] = None
) -> Tuple[Set, Union[int, float]]:
    """
    Find minimum weighted set of vertices covering all odd cycles.

    An odd cycle cover is a set of vertices such that removing them from the
    graph eliminates all cycles with odd length.

    :param ugraph: The input undirected graph.
    :type ugraph: nx.Graph
    :param weight: A mapping from vertices to their weights.
    :type weight: MutableMapping
    :param coverset: Optional initial odd cycle cover (default: empty set).
    :type coverset: Optional[Set]

    :return: A tuple of (minimum odd cycle cover set, total weight).
    :rtype: Tuple[Set, Union[int, float]]
    """
    if coverset is None:
        coverset = set()

    def find_odd_cycle() -> Any:
        for info, parent, child in _generic_bfs_cycle(ugraph, coverset):
            _, depth_child = info[child]
            _, depth_parent = info[parent]
            if (depth_parent - depth_child) % 2 == 0:
                return _construct_cycle(info, parent, child)

    def violate() -> Generator:
        while True:
            S = find_odd_cycle()
            if S is None:
                break
            yield S

    return pd_cover(violate, weight, coverset)
