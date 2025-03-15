"""
Cover.py

This code implements several algorithms for solving different types of covering problems in graphs. The main purpose is to find minimal sets of vertices or edges that "cover" certain structures in a graph, such as all edges, cycles, or odd cycles.

The code takes various inputs depending on the specific function being used. Generally, it requires a graph structure (either a regular graph or a hypergraph), a weight mapping for the vertices, and sometimes an optional initial cover set. The graphs are typically represented using the NetworkX library (nx.Graph).

The outputs produced by these functions are usually a tuple containing two elements: a set representing the minimal cover found, and a number representing the total weight or cost of that cover.

The code achieves its purpose through several different algorithms, but they all follow a similar pattern called the primal-dual approximation method. This method iteratively builds a solution by selecting elements that violate certain conditions and adding them to the cover set.

Here's a breakdown of the main functions:

1. pd_cover: This is the core function that implements the primal-dual approximation algorithm. It takes a "violate" function that generates sets of violating elements, a weight mapping, and an initial solution set. It iteratively adds elements to the solution until no violations remain.

2. min_vertex_cover: This function finds a minimum weighted vertex cover in a graph. It uses pd_cover with a violate function that yields edges not covered by the current solution.

3. min_hyper_vertex_cover: Similar to min_vertex_cover, but works on hypergraphs where edges can connect more than two vertices.

4. min_cycle_cover: This function finds a minimum weighted set of vertices that cover all cycles in a graph. It uses a breadth-first search to find cycles and then uses pd_cover to select vertices that break these cycles.

5. min_odd_cycle_cover: Similar to min_cycle_cover, but specifically targets odd cycles in the graph.

The code uses several important data structures and algorithms. Graphs are represented using NetworkX, which provides efficient graph operations. The algorithms make heavy use of sets for storing covers and dictionaries for storing weights and other information. The cycle-finding algorithms use breadth-first search and clever bookkeeping to efficiently detect cycles in the graph.

Overall, this code provides a toolkit for solving various covering problems on graphs, which have applications in many areas of computer science and operations research. The algorithms implemented here provide approximate solutions to these problems, which are often NP-hard and thus difficult to solve exactly for large instances.
"""

import copy
from collections import deque
from typing import (
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
    The function `pd_cover` implements a primal-dual approximation algorithm for covering problems.

    :param violate: The `violate` parameter is a callable function or oracle that returns a set of
        violate elements. It is used to generate sets of elements that violate the current solution. Each
        set represents a potential improvement to the solution

    :type violate: Callable

    :param weight: The `weight` parameter is a dictionary that represents the weight of each element.
        The keys of the dictionary are the elements, and the values are their corresponding weights

    :type weight: MutableMapping

    :param soln: The `soln` parameter is a set that represents the current solution set. It initially
        contains no elements, and elements are added to it during the algorithm

    :type soln: Set

    :return: a tuple containing the updated solution set and the total primal cost.

    Examples:
        >>> def violate_graph() -> Generator:
        ...     yield [0, 1]
        ...     yield [0, 2]
        ...     yield [1, 2]
        >>> weight = {0: 1, 1: 2, 2: 3}
        >>> soln = set()
        >>> pd_cover(violate_graph, weight, soln)
        ({0, 1}, 4)
    """
    total_prml_cost = 0
    total_dual_cost = 0
    gap = copy.copy(weight)
    for S in violate():
        min_vtx = min(S, key=lambda vtx: gap[vtx])
        min_val = gap[min_vtx]
        soln.add(min_vtx)
        total_prml_cost += weight[min_vtx]
        total_dual_cost += min_val
        for vtx in S:
            gap[vtx] -= min_val
    assert total_dual_cost <= total_prml_cost
    return soln, total_prml_cost


def min_vertex_cover(
    ugraph: nx.Graph, weight: MutableMapping, coverset: Optional[Set] = None
) -> Tuple[Set, Union[int, float]]:
    r"""
    The `min_vertex_cover` function performs minimum weighted vertex cover using a primal-dual
    approximation algorithm (without post-processing).

    :param ugraph: The parameter `ugraph` is a `nx.Graph` object, which represents the input graph. It is an
        undirected graph where each edge represents a connection between two vertices

    :type ugraph: nx.Graph

    :param weight: The `weight` parameter is a dictionary that assigns a weight to each vertex in the
        graph. The weights are used to determine the minimum weighted vertex cover

    :type weight: MutableMapping

    :param coverset: The `coverset` parameter is an optional set that represents the current vertex
        cover solution. It is used to keep track of the vertices that are included in the cover. If no
        `coverset` is provided, an empty set is used as the initial cover

    :type coverset: Optional[Set]

    :return: The function `min_vertex_cover` returns a tuple containing two elements. The first element
        is a set representing the minimum weighted vertex cover, and the second element is either an integer
        or a float representing the weight of the minimum vertex cover.

    .. svgbob::
       :align: center

        "({b, d, e}, 3)"

        b     c     d     e
        #-----o-----#-----o
        |      \   / \
        |       \ /   \
        o        #-----o
        a        e     f

    Examples:
        >>> ugraph = nx.Graph()
        >>> ugraph.add_edges_from([(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4)])
        >>> weight = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1}
        >>> soln = set()
        >>> min_vertex_cover(ugraph, weight, soln)
        ({0, 1, 2, 3}, 4)
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
    hyprgraph, weight: MutableMapping, coverset: Optional[Set] = None
) -> Tuple[Set, Union[int, float]]:
    """
    The `min_hyper_vertex_cover` function performs minimum weighted vertex cover using a primal-dual
    approximation algorithm (without post-processing).

    :param hyprgraph: The `hyprgraph` parameter represents a hypergraph, which is a generalization of a
        graph where an edge can connect more than two vertices. It is likely represented as a data structure
        that contains information about the vertices and edges of the hypergraph

    :param weight: The `weight` parameter is a mutable mapping that assigns a weight to each vertex in
        the hypergraph. It is used to determine the minimum weighted vertex cover

    :type weight: MutableMapping

    :param coverset: The `coverset` parameter is an optional set that represents the current vertex
        cover. It contains the vertices that have been selected as part of the cover. If no `coverset` is
        provided, it defaults to an empty set

    :type coverset: Optional[Set]

    :return: The function `min_hyper_vertex_cover` returns a tuple containing two elements. The first
        element is a set representing the minimum weighted vertex cover, and the second element is either an
        integer or a float representing the weight of the vertex cover.

    .. svgbob::
       :align: center

        "({b, d, g, h}, 4)"

        a       b        e       g
        o-------#-----+--o-------#
                      |  |
                   ,--)--'
                   |  |
                   |  `--.
                   |     |
        o-------#--+-----o-------#
        c       d        f       h

    """
    if coverset is None:
        coverset = set()

    def violate_netlist() -> Generator:
        for net in hyprgraph.nets:
            if any(vtx in coverset for vtx in hyprgraph.ugraph[net]):
                continue
            yield hyprgraph.ugraph[net]

    return pd_cover(violate_netlist, weight, coverset)


def _construct_cycle(info: Dict, parent, child) -> Deque:
    """
    The `_construct_cycle` function constructs a cycle by traversing the parent-child relationship in a
    dictionary.

    :param info: The `info` parameter is a dictionary that contains information about the nodes in a
        graph. Each key in the dictionary represents a node, and the corresponding value is a tuple
        containing two elements: the parent node and the depth of the node

    :type info: Dict

    :param parent: The parent parameter represents the parent node in a graph or tree structure

    :param child: The `child` parameter represents a node in a graph that is connected to the `parent`
        node

    :return: a deque object.
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
    # depth_now == depth
    while node_a != node_b:
        S.append(node_a)
        S.appendleft(node_b)
        node_a, _ = info[node_a]
        node_b, _ = info[node_b]
    S.appendleft(node_b)
    return S


def min_cycle_cover(
    ugraph: nx.Graph, weight: MutableMapping, coverset: Optional[Set] = None
) -> Tuple[Set, Union[int, float]]:
    r"""
    The `min_cycle_cover` function performs minimum cycle cover using a primal-dual approximation
        algorithm (without post-processing).

    :param ugraph: The `ugraph` parameter is a `nx.Graph` object representing the input graph. It contains the
        nodes and edges of the graph

    :type ugraph: nx.Graph

    :param weight: The `weight` parameter is a dictionary that assigns a weight to each node in the
        graph. The weights are used to determine the minimum cycle cover

    :type weight: MutableMapping

    :param coverset: The `coverset` parameter is an optional set that contains the nodes that are
        already covered by previous cycles. It is used to keep track of the nodes that have already been
        included in the minimum cycle cover. If no `coverset` is provided, it is initialized as an empty set

    :type coverset: Optional[Set]

    :return: The function `min_cycle_cover` returns a tuple containing a set and either an integer or a
        float. The set represents the minimum cycle cover, and the integer or float represents the weight of
        the minimum cycle cover.

    .. svgbob::
       :align: center

        "({c, d}, 2)"

        a     b     c
        o-----o-----#
         \   / \     \
          \ /   \     \
           #-----o-----o
           d     e     f

    Examples:
        >>> ugraph = nx.Graph()
        >>> ugraph.add_edges_from([(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4)])
        >>> weight = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1}
        >>> soln = set()
        >>> min_cycle_cover(ugraph, weight, soln)
        ({0, 1, 2}, 3)
    """
    if coverset is None:
        coverset = set()

    def find_cycle():
        for info, parent, child in _generic_bfs_cycle(ugraph, coverset):
            return _construct_cycle(info, parent, child)

    def violate() -> Generator:
        while True:
            S = find_cycle()
            if S is None:
                break
            yield S

    return pd_cover(violate, weight, coverset)


def _generic_bfs_cycle(ugraph: nx.Graph, coverset: Set) -> Generator:
    """
    The function `_generic_bfs_cycle` performs a breadth-first search on a graph to find cycles,
    excluding nodes in a given `coverset`.

    :param ugraph: The parameter `ugraph` is a graph object that represents a directed graph. It should have a
        method `neighbors(node)` that returns the neighbors of a given node in the graph. The graph can be
        represented using any graph library or data structure that supports this method

    :param coverset: The `coverset` parameter is a set of nodes that should be excluded from the BFS
        traversal. These nodes will not be considered as potential starting points for the BFS algorithm
    """
    depth_limit = len(ugraph)
    neighbors = ugraph.neighbors
    nodelist = list(ugraph.nodes())
    for source in nodelist:
        if source in coverset:
            continue
        info = {source: (source, depth_limit)}
        queue = deque([source])
        while queue:
            parent = queue.popleft()
            succ, depth_now = info[parent]
            for child in neighbors(parent):
                if child in coverset:
                    continue
                if child not in info:
                    info[child] = (parent, depth_now - 1)
                    queue.append(child)
                    continue
                if succ == child:
                    continue
                # cycle found
                yield info, parent, child


def min_odd_cycle_cover(
    ugraph: nx.Graph, weight: MutableMapping, coverset: Optional[Set] = None
) -> Tuple[Set, Union[int, float]]:
    r"""
    The `min_odd_cycle_cover` function performs minimum odd cycle cover using a primal-dual
    approximation algorithm (without post-processing).

    :param ugraph: The `ugraph` parameter is a `nx.Graph` object representing the input graph. It is used to
        define the graph structure and find cycles in the graph

    :type ugraph: nx.Graph

    :param weight: The `weight` parameter is a dictionary that assigns a weight to each node in the
        graph

    :type weight: MutableMapping

    :param coverset: The `coverset` parameter is an optional set that represents the initial set of
        vertices that are covered by the minimum odd cycle cover. This set can be empty if no vertices are
        initially covered

    :type coverset: Optional[Set]

    :return: The function `min_odd_cycle_cover` returns a tuple containing a set and either an integer
        or a float. The set represents the minimum odd cycle cover, and the integer or float represents the
        weight of the cover.

    .. svgbob::
       :align: center

        "({d}, 1)"

        a     b     c
        o-----o-----o
         \   / \     \
          \ /   \     \
           #-----o-----o
           d     e     f

    Examples:
        >>> ugraph = nx.Graph()
        >>> ugraph.add_edges_from([(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4)])
        >>> weight = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1}
        >>> soln = set()
        >>> min_odd_cycle_cover(ugraph, weight, soln)
        ({0, 1, 2}, 3)
    """
    if coverset is None:
        coverset = set()

    def find_odd_cycle():
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
