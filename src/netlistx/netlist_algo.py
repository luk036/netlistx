"""
Min Maximal Matching Algorithm

This code implements a function called min_maximal_matching which is designed to find a minimum weighted maximal matching in a hypergraph. Let's break down what this means and how the function works.

The purpose of this code is to select a set of edges (called "nets" in this context) from a hypergraph in such a way that the total weight of the selected edges is minimized, while ensuring that no more edges can be added to the set without overlapping with already selected edges. This is useful in various optimization problems, such as circuit design or resource allocation.

The function takes four inputs:

1. hyprgraph: A representation of the hypergraph structure.
2. weight: A dictionary-like object that assigns weights to each edge in the hypergraph.
3. matchset: An optional set of pre-selected edges (defaults to an empty set if not provided).
4. dep: An optional set of vertices that are already covered by the matching (defaults to an empty set if not provided).

The output of the function is a tuple containing two elements:

1. The final set of matched edges (nets).
2. The total weight of the selected matching.

The algorithm works by iteratively selecting edges to add to the matching. It starts with an empty matching (unless a pre-defined matching is provided) and gradually builds it up. Here's a simplified explanation of how it achieves its purpose:

1. It initializes some variables, including a copy of the weight dictionary called gap.
2. It then loops through all the edges (nets) in the hypergraph.
3. For each edge, it checks if any of its vertices are already covered by the current matching. If so, it skips this edge.
4. If the edge is not skipped, it looks for the edge with the minimum weight (considering the current gap values) that connects to any of the vertices of the current edge.
5. It adds this minimum-weight edge to the matching, updates the total cost, and marks all its vertices as covered.
6. It then updates the gap values for the remaining edges to reflect this selection.

The algorithm uses a primal-dual approach, which means it maintains two cost values: a primal cost (the actual weight of the selected edges) and a dual cost (a lower bound on the optimal solution). This helps ensure that the algorithm produces a solution that is within a certain factor of the optimal solution.

Some important logic flows in this code include the selection of the minimum-weight edge, the updating of the gap values, and the maintenance of the covered vertices set. These steps work together to gradually build up the matching while trying to minimize the total weight.

In summary, this algorithm provides a way to find a good (though not necessarily optimal) set of non-overlapping edges in a hypergraph, with the goal of minimizing the total weight of the selected edges. This can be useful in various optimization scenarios where you need to select a set of items that don't conflict with each other while minimizing some cost metric.
"""

import copy
from typing import MutableMapping, Optional, Set, Tuple, Union

from .netlist import Netlist


def min_maximal_matching(
    hyprgraph: Netlist,
    weight: MutableMapping,
    matchset: Optional[Set] = None,
    dep: Optional[Set] = None,
) -> Tuple[Set, Union[int, float]]:
    r"""
    The `min_maximal_matching` function performs minimum weighted maximal matching using a primal-dual
    approximation algorithm.

    :param hyprgraph: The `hyprgraph` parameter represents a hypergraph, which is a generalization of a
        graph where an edge can connect more than two vertices. It is not clear from the code snippet what
        the exact data structure of the hypergraph is, but it likely contains information about the vertices
        and edges of

    :param weight: The `weight` parameter is a mutable mapping that represents the weights of the
        hypergraph edges. It is used to determine the weight of each edge in the matching. The keys of the
        `weight` mapping correspond to the hypergraph edges, and the values represent their weights

    :type weight: MutableMapping

    :param matchset: The `matchset` parameter is a set that represents the pre-defined matching. It
        contains the hyperedges (nets) that are already matched

    :type matchset: Optional[Set]

    :param dep: The `dep` parameter is a set that represents the set of vertices that are covered by the
        current matching. It is initially set to an empty set, and is updated during the execution of the
        algorithm

    :type dep: Optional[Set]

    :return: The function `min_maximal_matching` returns a tuple containing the matchset (a set of
        matched elements) and the total primal cost (an integer or float representing the total weight of
        the matching).

    .. svgbob::
       :align: center

        a       b        e       g
        o=======o-----+--o=======o
                      |  |
                   ,--)--'
                   |  |
                   |  `--.
                   |     |
        o=======o--+-----o=======o
        c       d        f       h

    """
    if matchset is None:
        matchset = set()
    if dep is None:
        dep = set()

    def cover(net):
        for vtx in hyprgraph.ugraph[net]:
            dep.add(vtx)

    def any_of_dep(net):
        return any(vtx in dep for vtx in hyprgraph.ugraph[net])

    total_prml_cost = 0
    total_dual_cost = 0

    gap = copy.copy(weight)
    for net in hyprgraph.nets:
        if any_of_dep(net):
            continue
        if net in matchset:  # pre-define matching
            # cover(net)
            continue
        min_val = gap[net]
        min_net = net
        for vtx in hyprgraph.ugraph[net]:
            for net2 in hyprgraph.ugraph[vtx]:
                if any_of_dep(net2):
                    continue
                if min_val > gap[net2]:
                    min_val = gap[net2]
                    min_net = net2
        cover(min_net)
        matchset.add(min_net)
        total_prml_cost += weight[min_net]
        total_dual_cost += min_val
        if min_net == net:
            continue
        gap[net] -= min_val
        for vtx in hyprgraph.ugraph[net]:
            for net2 in hyprgraph.ugraph[vtx]:
                # if net2 == net:
                #     continue
                gap[net2] -= min_val

    assert total_dual_cost <= total_prml_cost
    return matchset, total_prml_cost
