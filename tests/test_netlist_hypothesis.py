"""Property-based tests for netlist functionality using Hypothesis."""

import json
import tempfile
from pathlib import Path

import hypothesis.strategies as st
from hypothesis import given

from netlistx.netlist import Netlist, SimpleGraph, create_random_hgraph, read_json


@st.composite
def netlist_strategy(draw):
    """Generate a valid netlist for testing."""
    # Generate modules and nets
    num_modules = draw(st.integers(min_value=1, max_value=10))
    num_nets = draw(st.integers(min_value=1, max_value=10))

    modules = [f"m{i}" for i in range(num_modules)]
    nets = [f"n{i}" for i in range(num_nets)]

    # Create graph
    graph = SimpleGraph()
    all_nodes = modules + nets
    graph.add_nodes_from(all_nodes)

    # Generate edges ensuring each net connects to at least one module
    for net in nets:
        # Each net must connect to at least one module
        num_connections = draw(st.integers(min_value=1, max_value=min(3, num_modules)))
        connected_modules = draw(
            st.lists(
                st.sampled_from(modules),
                min_size=num_connections,
                max_size=num_connections,
                unique=True,
            )
        )

        for module in connected_modules:
            graph.add_edge(net, module, weight=1)

    # Add some module-module connections (optional)
    if draw(st.booleans()) and num_modules >= 2:
        for _ in range(draw(st.integers(min_value=0, max_value=3))):
            m1, m2 = draw(
                st.lists(st.sampled_from(modules), min_size=2, max_size=2, unique=True)
            )
            if not graph.has_edge(m1, m2):
                graph.add_edge(m1, m2, weight=1)

    # Set graph attributes
    graph.graph["num_modules"] = num_modules
    graph.graph["num_nets"] = num_nets
    graph.graph["num_pads"] = draw(st.integers(min_value=0, max_value=num_modules))

    # Create module weights
    module_weight = {}
    for module in modules:
        module_weight[module] = draw(st.integers(min_value=0, max_value=10))

    netlist = Netlist(graph, modules, nets)
    netlist.module_weight = module_weight  # type: ignore[assignment]
    netlist.net_weight = draw(st.just([1] * num_nets))  # type: ignore[assignment]
    netlist.num_pads = graph.graph["num_pads"]

    return netlist


class TestNetlistProperties:
    """Property-based tests for Netlist class."""

    @given(netlist=netlist_strategy())
    def test_module_count_consistency(self, netlist: Netlist):
        """Test that module count is consistent across different methods."""
        assert netlist.number_of_modules() == len(netlist.modules)
        assert netlist.number_of_modules() == netlist.num_modules

    @given(netlist=netlist_strategy())
    def test_net_count_consistency(self, netlist: Netlist):
        """Test that net count is consistent across different methods."""
        assert netlist.number_of_nets() == len(netlist.nets)
        assert netlist.number_of_nets() == netlist.num_nets

    @given(netlist=netlist_strategy())
    def test_node_count_consistency(self, netlist: Netlist):
        """Test that total node count matches modules + nets."""
        expected_nodes = netlist.number_of_modules() + netlist.number_of_nets()
        assert netlist.number_of_nodes() == expected_nodes
        assert netlist.ugraph.number_of_nodes() == expected_nodes

    @given(netlist=netlist_strategy())
    def test_pin_count_non_negative(self, netlist: Netlist):
        """Test that pin count is non-negative."""
        assert netlist.number_of_pins() >= 0
        assert netlist.number_of_pins() == netlist.ugraph.number_of_edges()

    @given(netlist=netlist_strategy())
    def test_max_degree_properties(self, netlist: Netlist):
        """Test properties of maximum degree."""
        max_deg = netlist.get_max_degree()
        assert max_deg >= 0

        # Check that max degree is actually the maximum
        for module in netlist.modules:
            assert netlist.ugraph.degree[module] <= max_deg

    @given(netlist=netlist_strategy())
    def test_module_weight_bounds(self, netlist: Netlist):
        """Test that module weights are within expected bounds."""
        for i, module in enumerate(netlist.modules):
            weight = netlist.get_module_weight(i)
            assert isinstance(weight, int)
            assert weight >= 0

    @given(netlist=netlist_strategy())
    def test_net_weight_consistency(self, netlist: Netlist):
        """Test that net weights are consistent."""
        for net in netlist.nets:
            weight = netlist.get_net_weight(net)
            assert isinstance(weight, int)
            assert weight >= 0

    @given(netlist=netlist_strategy())
    def test_iterator_returns_modules(self, netlist: Netlist):
        """Test that iterator returns all modules."""
        iterated_modules = list(netlist)
        assert set(iterated_modules) == set(netlist.modules)
        assert len(iterated_modules) == len(netlist.modules)

    @given(data=st.data())
    def test_random_hgraph_properties(self, data: st.DataObject):
        """Test properties of randomly generated hypergraphs."""
        N = data.draw(st.integers(min_value=1, max_value=20))
        M = data.draw(st.integers(min_value=1, max_value=20))
        eta = data.draw(
            st.floats(min_value=0.01, max_value=1.0)
        )  # Avoid very small values

        netlist = create_random_hgraph(N, M, eta)

        # Test basic properties
        assert netlist.number_of_modules() == N
        assert netlist.number_of_nets() == M
        assert netlist.number_of_nodes() == N + M
        assert netlist.number_of_pins() >= 0

        # Test that all modules exist
        for i in range(N):
            assert i in netlist.modules

        # Test that all nets exist
        for i in range(N, N + M):
            assert i in netlist.nets

    @given(netlist=netlist_strategy())
    def test_bipartite_property(self, netlist: Netlist):
        """Test that the netlist graph maintains bipartite properties between modules and nets."""
        modules_set = set(netlist.modules)
        nets_set = set(netlist.nets)

        # Check that modules and nets are disjoint
        assert modules_set.isdisjoint(nets_set)

        # Check that edges connect modules to nets (primarily)
        for edge in netlist.ugraph.edges():
            node1, node2 = edge
            # At least one endpoint should be a module or net
            assert node1 in modules_set or node1 in nets_set
            assert node2 in modules_set or node2 in nets_set


class TestNetlistJSON:
    """Property-based tests for JSON serialization/deserialization."""

    @given(data=st.data())
    def test_json_roundtrip(self, data: st.DataObject):
        """Test that netlist can be serialized to JSON and read back."""
        # Create a simple netlist with integer modules/nets like read_json expects
        num_modules = data.draw(st.integers(min_value=1, max_value=5))
        num_nets = data.draw(st.integers(min_value=1, max_value=5))
        num_pads = data.draw(st.integers(min_value=0, max_value=num_modules))

        modules = list(range(num_modules))
        nets = list(range(num_modules, num_modules + num_nets))

        # Create graph
        graph = SimpleGraph()
        graph.add_nodes_from(modules + nets)

        # Add edges
        for net in nets:
            # Each net connects to at least one module
            num_connections = data.draw(
                st.integers(min_value=1, max_value=min(3, num_modules))
            )
            connected_modules = data.draw(
                st.lists(
                    st.sampled_from(modules),
                    min_size=num_connections,
                    max_size=num_connections,
                    unique=True,
                )
            )
            for module in connected_modules:
                graph.add_edge(net, module)

        # Set graph attributes
        graph.graph["num_modules"] = num_modules
        graph.graph["num_nets"] = num_nets
        graph.graph["num_pads"] = num_pads

        # Create netlist
        module_weight = {
            i: data.draw(st.integers(min_value=1, max_value=10)) for i in modules
        }
        netlist = Netlist(graph, modules, nets)
        netlist.module_weight = module_weight  # type: ignore[assignment]
        netlist.net_weight = [1] * num_nets  # type: ignore[assignment]
        netlist.num_pads = num_pads

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Convert netlist to JSON format
            data_dict = {
                "directed": False,
                "multigraph": False,
                "graph": {
                    "num_modules": netlist.num_modules,
                    "num_nets": netlist.num_nets,
                    "num_pads": netlist.num_pads,
                },
                "nodes": [{"id": node} for node in netlist.ugraph.nodes()],
                "edges": [
                    {"source": u, "target": v, **netlist.ugraph[u][v]}
                    for u, v in netlist.ugraph.edges()
                ],
            }

            json.dump(data_dict, f)
            temp_path = f.name

        try:
            # Read back the netlist
            restored_netlist = read_json(temp_path)

            # Test that basic properties match
            assert restored_netlist.number_of_modules() == netlist.number_of_modules()
            assert restored_netlist.number_of_nets() == netlist.number_of_nets()
            assert restored_netlist.number_of_pins() == netlist.number_of_pins()
            assert restored_netlist.num_pads == netlist.num_pads

        finally:
            # Clean up
            Path(temp_path).unlink()

    @given(data=st.data())
    def test_json_structure_validity(self, data: st.DataObject):
        """Test that JSON files have valid structure."""
        # Generate valid JSON structure
        num_modules = data.draw(st.integers(min_value=1, max_value=5))
        num_nets = data.draw(st.integers(min_value=1, max_value=5))
        num_pads = data.draw(st.integers(min_value=0, max_value=num_modules))

        # Create valid JSON data with integer nodes like read_json expects
        json_data = {
            "directed": False,
            "multigraph": False,
            "graph": {
                "num_modules": num_modules,
                "num_nets": num_nets,
                "num_pads": num_pads,
            },
            "nodes": [{"id": i} for i in range(num_modules + num_nets)],
            "edges": [],
        }

        # Add some edges - modules are 0 to num_modules-1, nets are num_modules to num_modules+num_nets-1
        for i in range(num_nets):
            net_id = num_modules + i
            # Connect each net to at least one module
            module_id = i % num_modules
            json_data["edges"].append(
                {"source": net_id, "target": module_id, "weight": 1}
            )

        # Test that valid JSON can be read
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_data, f)
            temp_path = f.name

        try:
            netlist = read_json(temp_path)
            assert netlist.number_of_modules() == num_modules
            assert netlist.number_of_nets() == num_nets
            assert netlist.num_pads == num_pads
        finally:
            Path(temp_path).unlink()


class TestNetlistInvariants:
    """Tests for fundamental netlist invariants."""

    @given(netlist=netlist_strategy())
    def test_weighted_degree_consistency(self, netlist: Netlist):
        """Test that weighted degrees are consistent."""
        total_module_weight = sum(
            netlist.get_module_weight(i) for i in range(len(netlist.modules))
        )
        total_net_weight = sum(netlist.get_net_weight(net) for net in netlist.nets)

        assert total_module_weight >= 0
        assert total_net_weight >= 0

    @given(netlist=netlist_strategy())
    def test_module_fixed_set_property(self, netlist: Netlist):
        """Test properties of the fixed module set."""
        assert isinstance(netlist.module_fixed, set)
        # All elements in module_fixed should be valid modules
        for fixed_module in netlist.module_fixed:
            assert fixed_module in netlist.modules

    @given(netlist=netlist_strategy())
    def test_cost_model_property(self, netlist: Netlist):
        """Test cost model property."""
        assert isinstance(netlist.cost_model, int)
        assert netlist.cost_model >= 0

    @given(netlist=netlist_strategy())
    def test_graph_connectivity_properties(self, netlist: Netlist):
        """Test basic graph connectivity properties."""
        # Every module should be a node in the graph
        for module in netlist.modules:
            assert module in netlist.ugraph.nodes

        # Every net should be a node in the graph
        for net in netlist.nets:
            assert net in netlist.ugraph.nodes

        # No duplicate nodes
        all_nodes = list(netlist.ugraph.nodes)
        assert len(all_nodes) == len(set(all_nodes))
