"""
Minimum vertex cover for weighted netlist.
"""
import copy
from typing import Union, Set, Tuple, Optional
from typing import MutableMapping


def min_maximal_matching(
    hyprgraph,
    weight: MutableMapping,
    matchset: Optional[Set] = None,
    dep: Optional[Set] = None,
) -> Tuple[Set, Union[int, float]]:
    """
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
        o=======o-----*--o=======o
                      |  |
                   ,--)--'
                   |  |
                   |  `--.
                   |     |
        o=======o--*-----o=======o
        c       d        f       h

    """
    if matchset is None:
        matchset = set()
    if dep is None:
        dep = set()

    def cover(net):
        for vtx in hyprgraph.gra[net]:
            dep.add(vtx)

    def any_of_dep(net):
        return any(vtx in dep for vtx in hyprgraph.gra[net])

    total_primal_cost = 0
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
        for vtx in hyprgraph.gra[net]:
            for net2 in hyprgraph.gra[vtx]:
                if any_of_dep(net2):
                    continue
                if min_val > gap[net2]:
                    min_val = gap[net2]
                    min_net = net2
        cover(min_net)
        matchset.add(min_net)
        total_primal_cost += weight[min_net]
        total_dual_cost += min_val
        if min_net == net:
            continue
        gap[net] -= min_val
        for vtx in hyprgraph.gra[net]:
            for net2 in hyprgraph.gra[vtx]:
                # if net2 == net:
                #     continue
                gap[net2] -= min_val

    assert total_dual_cost <= total_primal_cost
    return matchset, total_primal_cost
