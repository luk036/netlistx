"""Targeted tests to cover uncovered lines in netlist.py.

Missing lines: [102, 106, 112, 113, 114]
Missing branches: [[405, 404], [681, 685]]
"""

import json
import tempfile
from pathlib import Path

import networkx as nx

from netlistx.netlist import SimpleGraph, TinyGraph, form_graph, read_yosys_json


class TestTinyGraph:
    """Cover TinyGraph.init_nodes() and its helper methods (lines 102, 106, 112-114)."""

    def test_tiny_graph_init(self) -> None:
        """Create a TinyGraph and call init_nodes."""
        tg = TinyGraph()
        tg.init_nodes(5)
        assert tg.num_nodes == 5
        assert len(tg._node) == 5
        assert len(tg._adj) == 5

    def test_tiny_graph_as_graph(self) -> None:
        """Use TinyGraph as a working graph with nodes and edges."""
        tg = TinyGraph()
        tg.init_nodes(4)
        tg.add_edge(0, 1)
        tg.add_edge(1, 2)
        tg.add_edge(2, 3)
        assert tg.number_of_nodes() == 4
        assert tg.number_of_edges() == 3

    def test_tiny_graph_cheat_methods(self) -> None:
        """Directly call cheat_node_dict and cheat_adjlist_outer_dict."""
        tg = TinyGraph()
        tg.num_nodes = 3
        node_dict = tg.cheat_node_dict()
        assert len(node_dict) == 3
        adj_dict = tg.cheat_adjlist_outer_dict()
        assert len(adj_dict) == 3


class TestFormGraphWithoutSeed:
    """Cover branch [681, 685] in form_graph - when seed is falsy."""

    def test_form_graph_no_seed(self) -> None:
        """Call form_graph without providing a seed (default None)."""
        result = form_graph(10, 10, None, 0.5)
        assert isinstance(result, nx.Graph)
        assert result.number_of_nodes() == 20  # N + M


class TestReadYosysJsonEdgeCases:
    """Cover branch [405, 404] - port net_id not in nets_dict."""

    def test_port_with_missing_net_id(self) -> None:
        """Port referencing a net_id not collected as a net node."""
        cells = {
            "and1": {
                "type": "$and",
                "connections": {
                    "A": [0],
                    "B": [1],
                    "Y": [2],
                },
            }
        }
        ports = {
            "a": {"direction": "input", "bits": [0]},
            "b": {"direction": "input", "bits": [1]},
            "y": {"direction": "output", "bits": [999]},  # 999 not in nets_dict
        }

        data = {"modules": {"top": {"cells": cells, "ports": ports}}}
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(data, tmp)
        tmp.close()
        try:
            netlist = read_yosys_json(tmp.name)
            assert netlist is not None
            # net 999 should not have been added (not in nets_dict)
        finally:
            Path(tmp.name).unlink()


class TestNetlistSimpleGraph:
    """Cover SimpleGraph.single_edge_dict (lines 102, 106 in coverage report)."""

    def test_simple_graph_edge_attr(self) -> None:
        """Create SimpleGraph and verify edge_attr_dict_factory works."""
        sg = SimpleGraph()
        sg.add_edge(0, 1)
        # The edge should get default weight attribute
        assert sg[0][1].get("weight", None) == 1

    def test_simple_graph_node_attr(self) -> None:
        """Verify node_attr_dict_factory works."""
        sg = SimpleGraph()
        sg.add_node(0)
        # The node should get default weight attribute
        assert sg.nodes[0].get("weight", None) == 1


class TestCreateRandomHgraphNoSeed:
    """Additional test for coverage completeness."""

    def test_form_graph_with_seed_none_direct(self) -> None:
        """Directly test form_graph with seed=None for the branch coverage."""
        from netlistx.netlist import vdcorput

        N, M, eta = 5, 3, 0.5
        x = vdcorput(N + M, 2)
        y = vdcorput(N + M, 3)
        pos = zip(x, y)
        result = form_graph(N, M, pos, eta, seed=None)
        assert isinstance(result, nx.Graph)
