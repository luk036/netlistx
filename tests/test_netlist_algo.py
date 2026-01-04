from typing import Any

from netlistx.cover import min_hyper_vertex_cover
from netlistx.netlist_algo import min_maximal_matching


def test_min_vertex_cover(drawf_graph: Any) -> None:
    weight = {node: 1 for node in drawf_graph.modules}
    _, rslt = min_hyper_vertex_cover(drawf_graph, weight)
    assert rslt == 6


def test_min_maximal_matching(drawf_graph: Any) -> None:
    weight = {net: 1 for net in drawf_graph.nets}
    _, rslt = min_maximal_matching(drawf_graph, weight)
    assert rslt == 3


def test_min_maximal_matching2(p1_graph: Any) -> None:
    weight = {net: 1 for net in p1_graph.nets}
    _, rslt = min_maximal_matching(p1_graph, weight)
    assert rslt == 239


def test_min_maximal_matching_with_predefined_matchset(drawf_graph: Any) -> None:
    """Test min_maximal_matching with a pre-defined matchset to cover line 133."""
    weight = {net: 1 for net in drawf_graph.nets}
    # Add one net to the matchset beforehand
    predefined_net = list(drawf_graph.nets)[0]
    matchset = {predefined_net}
    result_matchset, cost = min_maximal_matching(drawf_graph, weight, matchset)
    # The predefined net should still be in the matchset
    assert predefined_net in result_matchset
    # Cost should be less than or equal to the total weight of all nets
    assert cost <= len(drawf_graph.nets)


def test_min_maximal_matching_with_predefined_dependents(drawf_graph: Any) -> None:
    """Test min_maximal_matching with pre-defined dependents."""
    weight = {net: 1 for net in drawf_graph.nets}
    # Add a module to the dependents set
    if drawf_graph.modules:
        dependent_module = list(drawf_graph.modules)[0]
        dependents = {dependent_module}
        result_matchset, cost = min_maximal_matching(
            drawf_graph, weight, dependents=dependents
        )
        # The result should be a valid matching
        assert isinstance(result_matchset, set)
        assert isinstance(cost, (int, float))


def test_min_maximal_matching_with_different_weights(drawf_graph: Any) -> None:
    """Test min_maximal_matching with different weights to trigger min_net != net case."""
    # Create weights that will encourage selecting different nets
    weight = {}
    for i, net in enumerate(drawf_graph.nets):
        weight[net] = i + 1  # Increasing weights

    result_matchset, cost = min_maximal_matching(drawf_graph, weight)
    # The result should be a valid matching
    assert isinstance(result_matchset, set)
    assert isinstance(cost, (int, float))
    # Cost should be the sum of weights of selected nets
    expected_cost = sum(weight[net] for net in result_matchset)
    assert cost == expected_cost
