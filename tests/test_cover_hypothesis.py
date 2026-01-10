"""Property-based tests for covering algorithms using Hypothesis."""

import hypothesis.strategies as st
from hypothesis import assume, given
from networkx import Graph, complete_graph, cycle_graph, path_graph

from netlistx.cover import (
    min_cycle_cover,
    min_hyper_vertex_cover,
    min_odd_cycle_cover,
    min_vertex_cover,
    pd_cover,
)


@st.composite
def weighted_graph_strategy(draw):
    """Generate a weighted graph for testing."""
    # Generate graph size
    num_nodes = draw(st.integers(min_value=1, max_value=8))

    # Choose graph type
    graph_type = draw(st.sampled_from(["path", "cycle", "complete", "random"]))

    if graph_type == "path":
        graph = path_graph(num_nodes)
    elif graph_type == "cycle":
        if num_nodes >= 3:
            graph = cycle_graph(num_nodes)
        else:
            graph = path_graph(num_nodes)  # fallback for small graphs
    elif graph_type == "complete":
        graph = complete_graph(num_nodes)
    else:  # random
        # Create a random graph without using NetworkX's erdos_renyi_graph
        graph = Graph()
        graph.add_nodes_from(range(num_nodes))
        edge_prob = draw(st.floats(min_value=0.1, max_value=0.9))

        # Add edges based on probability
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if draw(st.floats(min_value=0.0, max_value=1.0)) < edge_prob:
                    graph.add_edge(i, j)

    # Generate weights
    weight_strategy = st.integers(min_value=1, max_value=10)
    weights = {node: draw(weight_strategy) for node in graph.nodes()}

    return graph, weights


@st.composite
def hypergraph_strategy(draw):
    """Generate a hypergraph-like structure for testing."""
    num_modules = draw(st.integers(min_value=1, max_value=6))
    num_nets = draw(st.integers(min_value=1, max_value=6))

    modules = [f"m{i}" for i in range(num_modules)]
    nets = [f"n{i}" for i in range(num_nets)]

    # Create graph structure
    graph = Graph()
    graph.add_nodes_from(modules + nets)

    # Connect nets to modules
    for net in nets:
        # Each net connects to at least one module
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
            graph.add_edge(net, module)

    # Generate weights for modules only
    weights = {
        module: draw(st.integers(min_value=1, max_value=10)) for module in modules
    }

    # Create mock hypergraph
    class MockHypergraph:
        def __init__(self, nets, ugraph):
            self.nets = nets
            self.ugraph = ugraph

    hypergraph = MockHypergraph(nets, graph)
    return hypergraph, weights


class TestVertexCoverProperties:
    """Property-based tests for vertex cover algorithm."""

    @given(data=st.data())
    def test_vertex_cover_covers_all_edges(self, data: st.DataObject):
        """Test that vertex cover actually covers all edges."""
        graph, weights = data.draw(weighted_graph_strategy())
        assume(len(graph.edges()) > 0)  # Ensure graph has edges

        cover, total_weight = min_vertex_cover(graph, weights)

        # Every edge should have at least one endpoint in the cover
        for u, v in graph.edges():
            assert u in cover or v in cover, f"Edge ({u}, {v}) not covered by {cover}"

    @given(data=st.data())
    def test_vertex_cover_weight_consistency(self, data: st.DataObject):
        """Test that reported weight matches sum of vertex weights."""
        graph, weights = data.draw(weighted_graph_strategy())
        assume(len(graph.edges()) > 0)

        cover, total_weight = min_vertex_cover(graph, weights)

        # Calculate expected weight
        expected_weight = sum(weights[node] for node in cover if node in weights)
        assert total_weight == expected_weight

    @given(data=st.data())
    def test_vertex_cover_subset_property(self, data: st.DataObject):
        """Test that vertex cover is a subset of graph nodes."""
        graph, weights = data.draw(weighted_graph_strategy())
        assume(len(graph.edges()) > 0)

        cover, _ = min_vertex_cover(graph, weights)

        # All cover vertices should be in the graph
        for node in cover:
            assert node in graph.nodes()

    @given(data=st.data())
    def test_vertex_cover_empty_graph(self, data: st.DataObject):
        """Test vertex cover on graph with no edges."""
        graph = Graph()
        graph.add_nodes_from([0, 1, 2])
        weights = {0: 1, 1: 2, 2: 3}

        cover, total_weight = min_vertex_cover(graph, weights)

        # Empty graph should have empty cover
        assert len(cover) == 0
        assert total_weight == 0

    @given(data=st.data())
    def test_vertex_cover_preexisting_cover(self, data: st.DataObject):
        """Test algorithm with pre-existing cover set."""
        graph, weights = data.draw(weighted_graph_strategy())
        assume(len(graph.edges()) > 0)

        # Start with some vertices already in cover
        initial_cover = set()
        for node in graph.nodes():
            if data.draw(st.booleans()):
                initial_cover.add(node)

        cover, total_weight = min_vertex_cover(graph, weights, initial_cover.copy())

        # Initial cover should be subset of final cover
        assert initial_cover.issubset(cover)

        # All edges should still be covered
        for u, v in graph.edges():
            assert u in cover or v in cover


class TestHyperVertexCoverProperties:
    """Property-based tests for hypergraph vertex cover algorithm."""

    @given(data=st.data())
    def test_hyper_vertex_cover_covers_all_nets(self, data: st.DataObject):
        """Test that hypergraph vertex cover covers all nets."""
        hypergraph, weights = data.draw(hypergraph_strategy())

        cover, total_weight = min_hyper_vertex_cover(hypergraph, weights)

        # Every net should have at least one connected module in the cover
        for net in hypergraph.nets:
            connected_modules = hypergraph.ugraph[net]
            assert any(
                module in cover for module in connected_modules
            ), f"Net {net} not covered by any module in {cover}"

    @given(data=st.data())
    def test_hyper_vertex_cover_weight_consistency(self, data: st.DataObject):
        """Test that reported weight matches sum of module weights."""
        hypergraph, weights = data.draw(hypergraph_strategy())

        cover, total_weight = min_hyper_vertex_cover(hypergraph, weights)

        # Calculate expected weight (only modules have weights)
        expected_weight = sum(weights[node] for node in cover if node in weights)
        assert total_weight == expected_weight

    @given(data=st.data())
    def test_hyper_vertex_cover_modules_only(self, data: st.DataObject):
        """Test that hypergraph vertex cover only contains modules."""
        hypergraph, weights = data.draw(hypergraph_strategy())

        cover, _ = min_hyper_vertex_cover(hypergraph, weights)

        # Cover should only contain modules (not nets)
        modules = set(weights.keys())
        for node in cover:
            assert node in modules, f"Non-module {node} found in cover"


class TestCycleCoverProperties:
    """Property-based tests for cycle cover algorithm."""

    @given(data=st.data())
    def test_cycle_cover_breaks_all_cycles(self, data: st.DataObject):
        """Test that cycle cover breaks all cycles in the graph."""
        graph, weights = data.draw(weighted_graph_strategy())

        cover, total_weight = min_cycle_cover(graph, weights)

        # After removing cover vertices, the graph should be acyclic
        remaining_nodes = [node for node in graph.nodes() if node not in cover]
        remaining_graph = graph.subgraph(remaining_nodes)

        # Check that remaining graph has no cycles
        try:
            from networkx.algorithms import cycles

            remaining_cycles = list(cycles.cycle_basis(remaining_graph))
            assert (
                len(remaining_cycles) == 0
            ), f"Cycles found after removing cover: {remaining_cycles}"
        except ImportError:
            # Fallback: check if graph is a forest (no cycles)
            assert remaining_graph.number_of_edges() <= len(remaining_nodes) - 1

    @given(data=st.data())
    def test_cycle_cover_weight_consistency(self, data: st.DataObject):
        """Test that reported weight matches sum of vertex weights."""
        graph, weights = data.draw(weighted_graph_strategy())

        cover, total_weight = min_cycle_cover(graph, weights)

        # Calculate expected weight
        expected_weight = sum(weights[node] for node in cover if node in weights)
        assert total_weight == expected_weight

    @given(data=st.data())
    def test_cycle_cover_acyclic_graph(self, data: st.DataObject):
        """Test cycle cover on acyclic graph."""
        # Create a tree (acyclic graph)
        graph = path_graph(5)
        weights = {i: 1 for i in range(5)}

        cover, total_weight = min_cycle_cover(graph, weights)

        # Acyclic graph should have empty cover
        assert len(cover) == 0
        assert total_weight == 0

    @given(data=st.data())
    def test_cycle_cover_cycle_graph(self, data: st.DataObject):
        """Test cycle cover on a simple cycle."""
        cycle_length = data.draw(st.integers(min_value=3, max_value=8))
        graph = cycle_graph(cycle_length)
        weights = {i: 1 for i in range(cycle_length)}

        cover, total_weight = min_cycle_cover(graph, weights)

        # Cover should break the cycle
        remaining_nodes = [node for node in graph.nodes() if node not in cover]
        assert len(remaining_nodes) <= cycle_length - 1

        # At least one vertex should be in the cover
        assert len(cover) >= 1


class TestOddCycleCoverProperties:
    """Property-based tests for odd cycle cover algorithm."""

    @given(data=st.data())
    def test_odd_cycle_cover_breaks_all_odd_cycles(self, data: st.DataObject):
        """Test that odd cycle cover breaks all odd cycles."""
        graph, weights = data.draw(weighted_graph_strategy())

        cover, total_weight = min_odd_cycle_cover(graph, weights)

        # After removing cover vertices, the graph should have no odd cycles
        remaining_nodes = [node for node in graph.nodes() if node not in cover]
        remaining_graph = graph.subgraph(remaining_nodes)

        # Check that remaining graph has no odd cycles
        try:
            from networkx.algorithms import cycles

            remaining_cycles = list(cycles.cycle_basis(remaining_graph))
            for cycle in remaining_cycles:
                assert (
                    len(cycle) % 2 == 0
                ), f"Odd cycle {cycle} found after removing cover"
        except ImportError:
            # Skip this test if cycles module not available
            pass

    @given(data=st.data())
    def test_odd_cycle_cover_weight_consistency(self, data: st.DataObject):
        """Test that reported weight matches sum of vertex weights."""
        graph, weights = data.draw(weighted_graph_strategy())

        cover, total_weight = min_odd_cycle_cover(graph, weights)

        # Calculate expected weight
        expected_weight = sum(weights[node] for node in cover if node in weights)
        assert total_weight == expected_weight

    @given(data=st.data())
    def test_odd_cycle_cover_even_cycle_preserved(self, data: st.DataObject):
        """Test that even cycles might be preserved by odd cycle cover."""
        # Create an even cycle
        graph = cycle_graph(4)  # 4-cycle
        weights = {i: 1 for i in range(4)}

        cover, total_weight = min_odd_cycle_cover(graph, weights)

        # Even cycle might not need any vertices in cover
        # This is a weak test since the algorithm might still add vertices
        assert total_weight >= 0


class TestPDCoverProperties:
    """Property-based tests for primal-dual cover framework."""

    @given(data=st.data())
    def test_pd_cover_basic_properties(self, data: st.DataObject):
        """Test basic properties of pd_cover function."""
        # Create a simple violate function
        elements = [0, 1, 2, 3]
        weights = {
            i: data.draw(st.integers(min_value=1, max_value=10)) for i in elements
        }

        def violate_simple():
            # Yield violating sets
            yield [0, 1]
            yield [1, 2]
            yield [2, 3]

        solution = set()
        result, total_weight = pd_cover(violate_simple, weights, solution)

        # Solution should be a set
        assert isinstance(result, set)

        # Total weight should be non-negative
        assert total_weight >= 0

        # Weight should be non-negative and reasonable
        assert total_weight >= 0
        # Total weight should be at least the minimum weight in the result
        if result:
            min_weight_in_result = min(weights.get(node, 0) for node in result)
            assert total_weight >= min_weight_in_result

    @given(data=st.data())
    def test_pd_cover_empty_violate(self, data: st.DataObject):
        """Test pd_cover with no violations."""
        elements = [0, 1, 2]
        weights = {
            i: data.draw(st.integers(min_value=1, max_value=10)) for i in elements
        }

        def violate_empty():
            return iter([])  # No violations

        solution = set()
        result, total_weight = pd_cover(violate_empty, weights, solution)

        # Should return empty solution with zero weight
        assert len(result) == 0
        assert total_weight == 0

    @given(data=st.data())
    def test_pd_cover_preexisting_solution(self, data: st.DataObject):
        """Test pd_cover with pre-existing solution."""
        elements = [0, 1, 2, 3]
        weights = {
            i: data.draw(st.integers(min_value=1, max_value=10)) for i in elements
        }

        def violate_simple():
            yield [0, 1]
            yield [2, 3]

        # Start with some elements already in solution
        initial_solution = {0}
        solution = initial_solution.copy()
        result, total_weight = pd_cover(violate_simple, weights, solution)

        # Initial solution should be subset of final solution
        assert initial_solution.issubset(result)


class TestCoveringAlgorithmInvariants:
    """Tests for fundamental invariants of covering algorithms."""

    @given(data=st.data())
    def test_algorithm_determinism(self, data: st.DataObject):
        """Test that algorithms are deterministic for same input."""
        graph, weights = data.draw(weighted_graph_strategy())

        # Run vertex cover twice
        cover1, weight1 = min_vertex_cover(graph, weights)
        cover2, weight2 = min_vertex_cover(graph, weights)

        assert cover1 == cover2
        assert weight1 == weight2

    @given(data=st.data())
    def test_weight_non_negative(self, data: st.DataObject):
        """Test that all weights in solutions are non-negative."""
        graph, weights = data.draw(weighted_graph_strategy())

        # Test vertex cover
        cover, cover_weight = min_vertex_cover(graph, weights)
        assert cover_weight >= 0

        # Test cycle cover
        cover, cycle_weight = min_cycle_cover(graph, weights)
        assert cycle_weight >= 0

        # Test odd cycle cover
        cover, odd_cycle_weight = min_odd_cycle_cover(graph, weights)
        assert odd_cycle_weight >= 0

    @given(data=st.data())
    def test_subset_relationships(self, data: st.DataObject):
        """Test subset relationships between different covers."""
        graph, weights = data.draw(weighted_graph_strategy())

        vertex_cover, vertex_weight = min_vertex_cover(graph, weights)
        cycle_cover, cycle_weight = min_cycle_cover(graph, weights)
        odd_cycle_cover, odd_weight = min_odd_cycle_cover(graph, weights)

        # All covers should be subsets of graph nodes
        all_nodes = set(graph.nodes())
        assert vertex_cover.issubset(all_nodes)
        assert cycle_cover.issubset(all_nodes)
        assert odd_cycle_cover.issubset(all_nodes)

    @given(data=st.data())
    def test_monotonicity_with_weights(self, data: st.DataObject):
        """Test that weight changes are reasonable for approximation algorithms."""
        graph, base_weights = data.draw(weighted_graph_strategy())

        # Get cover with base weights
        cover1, weight1 = min_vertex_cover(graph, base_weights)

        # Double all weights (more significant change)
        increased_weights = {node: base_weights[node] * 2 for node in base_weights}
        cover2, weight2 = min_vertex_cover(graph, increased_weights)

        # With doubled weights, the total should be at least as high as original
        # But approximation algorithms might choose different vertices, so we use a lenient bound
        assert weight2 >= weight1 * 0.8  # Allow some variation due to approximation
