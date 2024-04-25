# -*- coding: utf-8 -*-
"""
Minimum vertex cover for weighed graphs.
1. Support Lazy evalution
"""
import copy
from typing import MutableMapping, Optional, Set, Tuple, Union


def min_vertex_cover_fast(
    ugraph, weight: MutableMapping, coverset: Optional[Set] = None
) -> Tuple[Set, Union[int, float]]:
    """
    The `min_vertex_cover_fast` function performs minimum weighted vertex cover using a primal-dual
    approximation algorithm (without post-processing).

    :param ugraph: ugraph is a NetworkX graph object representing the graph on which the minimum weighted
        vertex cover algorithm will be performed. It contains the nodes and edges of the graph

    :param weight: The `weight` parameter is a mutable mapping that represents the weight of each vertex
        in the graph. It is used to determine the minimum weighted vertex cover. The keys of the mapping are
        the vertices of the graph, and the values are the corresponding weights

    :type weight: MutableMapping

    :param coverset: The `coverset` parameter is an optional set that represents the current vertex
        cover. It is used to keep track of the vertices that are included in the cover. If no coverset is
        provided, a new empty set is created

    :type coverset: Optional[Set]

    :return: The function `min_vertex_cover_fast` returns a tuple containing the vertex cover set and
        the total weight of the vertex cover.

    .. svgbob::
       :align: center

        b     c     d     e
        #-----o-----#-----o
        |      \   / \       ({b, d, e}, 3)
        |       \ /   \
        o        #-----o
        a        e     f

    Examples:
        >>> import networkx as nx
        >>> from netlistx.graph_algo import min_vertex_cover_fast
        >>> ugraph = nx.Graph()
        >>> ugraph.add_edges_from([(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4)])
        >>> weight = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1}
        >>> coverset = set()
        >>> min_vertex_cover_fast(ugraph, weight, coverset)
        ({0, 1, 2, 3}, 4)
    """
    if coverset is None:
        coverset = set()

    total_dual_cost = 0  # for assertion
    total_prml_cost = 0
    gap = copy.copy(weight)

    for utx, vtx in ugraph.edges():
        if utx in coverset or vtx in coverset:
            continue
        if gap[utx] < gap[vtx]:
            utx, vtx = vtx, utx  # swap
        coverset.add(vtx)
        total_dual_cost += gap[vtx]
        total_prml_cost += weight[vtx]
        gap[utx] -= gap[vtx]
        gap[vtx] = 0

    assert total_dual_cost <= total_prml_cost
    return coverset, total_prml_cost


def min_maximal_independant_set(
    ugraph,
    weight: MutableMapping,
    indset: Optional[Set] = None,
    dep: Optional[Set] = None,
) -> Tuple[Set, Union[int, float]]:
    r"""
    The `min_maximal_independant_set` function performs minimum weighted maximal independent set using
    primal-dual algorithm.

    :param ugraph: ugraph is an undirected graph represented using the NetworkX library. It represents the
        graph structure and contains the vertices and edges of the graph

    :param weight: The `weight` parameter is a dictionary-like object that assigns a weight to each
        vertex in the graph. The keys of the dictionary represent the vertices, and the values represent
        their corresponding weights

    :type weight: MutableMapping

    :param indset: The `indset` parameter is a set that represents the current independent set. It is
        initially set to `None` and is updated during the execution of the `min_maximal_independent_set`
        function

    :type indset: Optional[Set]

    :param dep: The `dep` parameter is a set that represents the dependent vertices in the graph. These
        are the vertices that are not included in the independent set and are adjacent to vertices in the
        independent set. The `coverset` function is used to add a vertex and its adjacent vertices to the
        dependent set

    :type dep: Optional[Set]

    :return: The function `min_maximal_independant_set` returns a tuple containing the minimum weighted
        maximal independent set (indset) and the total primal cost (total_prml_cost).

    .. svgbob::
       :align: center

        0     2     4
        #-----o-----o
         \   / \   /    ({0, 3}, 2)
          \ /   \ /
           o-----#
           1     3

    Examples:
        >>> import networkx as nx
        >>> from netlistx.graph_algo import min_maximal_independant_set
        >>> ugraph = nx.Graph()
        >>> ugraph.add_edges_from([(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (2, 4), (3, 4)])
        >>> weight = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1}
        >>> indset = set()
        >>> dep = set()
        >>> min_maximal_independant_set(ugraph, weight, indset, dep)
        ({0, 3}, 2)
    """
    if indset is None:
        indset = set()
    if dep is None:
        dep = set()

    def coverset(utx):
        dep.add(utx)
        for vtx in ugraph[utx]:
            dep.add(vtx)

    gap = copy.copy(weight)
    total_prml_cost = 0
    total_dual_cost = 0
    for utx in ugraph:
        if utx in dep:
            continue
        if utx in indset:  # pre-define indepentant
            # coverset(utx)
            continue
        min_val = gap[utx]
        min_vtx = utx
        for vtx in ugraph[utx]:
            if vtx in dep:
                continue
            if min_val > gap[vtx]:
                min_val = gap[vtx]
                min_vtx = vtx
        indset.add(min_vtx)
        coverset(min_vtx)
        total_prml_cost += weight[min_vtx]
        total_dual_cost += min_val
        if min_vtx == utx:
            continue
        for vtx in ugraph[utx]:
            gap[vtx] -= min_val

    assert total_dual_cost <= total_prml_cost
    return indset, total_prml_cost
