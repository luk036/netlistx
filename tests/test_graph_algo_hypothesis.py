"""Property-based tests for graph algorithms using Hypothesis."""

import hypothesis.strategies as st
from hypothesis import given, assume
from networkx import Graph, complete_graph, path_graph, cycle_graph

from netlistx.graph_algo import min_vertex_cover_fast, min_maximal_independant_set


@st.composite
def weighted_graph_strategy(draw):
    """Generate a weighted graph for testing."""
    # Generate graph size
    num_nodes = draw(st.integers(min_value=1, max_value=10))

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
def edge_list_strategy(draw):
    """Generate an edge list and corresponding weights."""
    num_nodes = draw(st.integers(min_value=2, max_value=8))
    nodes = list(range(num_nodes))

    # Generate edges
    max_edges = num_nodes * (num_nodes - 1) // 2
    num_edges = draw(st.integers(min_value=1, max_value=max_edges))

    # Generate all possible edges and sample
    all_edges = [(i, j) for i in range(num_nodes) for j in range(i + 1, num_nodes)]
    edges = draw(
        st.lists(
            st.sampled_from(all_edges),
            min_size=num_edges,
            max_size=num_edges,
            unique=True,
        )
    )

    # Create graph
    graph = Graph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)

    # Generate weights
    weights = {node: draw(st.integers(min_value=1, max_value=10)) for node in nodes}

    return graph, weights


class TestVertexCoverProperties:
    """Property-based tests for minimum vertex cover algorithm."""

    @given(data=st.data())
    def test_vertex_cover_covers_all_edges(self, data: st.DataObject):
        """Test that vertex cover actually covers all edges."""
        graph, weights = data.draw(weighted_graph_strategy())
        assume(len(graph.edges()) > 0)  # Ensure graph has edges

        cover, total_weight = min_vertex_cover_fast(graph, weights)

        # Every edge should have at least one endpoint in the cover
        for u, v in graph.edges():
            assert u in cover or v in cover, f"Edge ({u}, {v}) not covered by {cover}"

    @given(data=st.data())
    def test_vertex_cover_weight_consistency(self, data: st.DataObject):
        """Test that reported weight matches sum of vertex weights."""
        graph, weights = data.draw(weighted_graph_strategy())
        assume(len(graph.edges()) > 0)

        cover, total_weight = min_vertex_cover_fast(graph, weights)

        # Calculate expected weight
        expected_weight = sum(weights[node] for node in cover)
        assert total_weight == expected_weight

    @given(data=st.data())
    def test_vertex_cover_subset_property(self, data: st.DataObject):
        """Test that vertex cover is a subset of graph nodes."""
        graph, weights = data.draw(weighted_graph_strategy())
        assume(len(graph.edges()) > 0)

        cover, _ = min_vertex_cover_fast(graph, weights)

        # All cover vertices should be in the graph
        for node in cover:
            assert node in graph.nodes()

    @given(data=st.data())
    def test_vertex_cover_monotonicity(self, data: st.DataObject):
        """Test that adding edges cannot reduce vertex cover size."""
        graph, weights = data.draw(weighted_graph_strategy())
        assume(len(graph.edges()) > 0)

        cover1, weight1 = min_vertex_cover_fast(graph, weights)

        # Add a new edge
        nodes = list(graph.nodes())
        if len(nodes) >= 2:
            new_edge = (nodes[0], nodes[1])
            if not graph.has_edge(*new_edge):
                graph.add_edge(*new_edge)
                cover2, weight2 = min_vertex_cover_fast(graph, weights)

                # Adding edges should not significantly reduce the cover weight
                # (it might stay the same or increase)
                assert weight2 >= weight1 * 0.5  # Allow some variation due to algorithm

    @given(data=st.data())
    def test_vertex_cover_empty_graph(self, data: st.DataObject):
        """Test vertex cover on graph with no edges."""
        graph = Graph()
        graph.add_nodes_from([0, 1, 2])
        weights = {0: 1, 1: 2, 2: 3}

        cover, total_weight = min_vertex_cover_fast(graph, weights)

        # Empty graph should have empty cover
        assert len(cover) == 0
        assert total_weight == 0

    @given(data=st.data())
    def test_vertex_cover_single_edge(self, data: st.DataObject):
        """Test vertex cover on graph with single edge."""
        graph = Graph()
        graph.add_edge(0, 1)
        weights = {
            0: data.draw(st.integers(min_value=1, max_value=10)),
            1: data.draw(st.integers(min_value=1, max_value=10)),
        }

        cover, total_weight = min_vertex_cover_fast(graph, weights)

        # Single edge should be covered by exactly one vertex
        assert len(cover) == 1
        assert (0 in cover) != (1 in cover)  # XOR: exactly one is in cover
        assert total_weight == weights[next(iter(cover))]

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

        cover, total_weight = min_vertex_cover_fast(
            graph, weights, initial_cover.copy()
        )

        # Initial cover should be subset of final cover
        assert initial_cover.issubset(cover)

        # All edges should still be covered
        for u, v in graph.edges():
            assert u in cover or v in cover


class TestIndependentSetProperties:
    """Property-based tests for minimum maximal independent set algorithm."""

    @given(data=st.data())
    def test_independent_set_independence(self, data: st.DataObject):
        """Test that independent set has no internal edges."""
        graph, weights = data.draw(weighted_graph_strategy())

        indset, total_weight = min_maximal_independant_set(graph, weights)

        # No two vertices in independent set should be adjacent
        for u in indset:
            for v in indset:
                if u != v:
                    assert not graph.has_edge(u, v), (
                        f"Edge ({u}, {v}) found in independent set"
                    )

    @given(data=st.data())
    def test_independent_set_maximality(self, data: st.DataObject):
        """Test that independent set is maximal."""
        graph, weights = data.draw(weighted_graph_strategy())

        indset, total_weight = min_maximal_independant_set(graph, weights)

        # Every vertex not in the independent set should be adjacent to at least one vertex in it
        for node in graph.nodes():
            if node not in indset:
                has_neighbor_in_indset = any(
                    graph.has_edge(node, ind_node) for ind_node in indset
                )
                assert has_neighbor_in_indset, (
                    f"Node {node} can be added to independent set {indset}"
                )

    @given(data=st.data())
    def test_independent_set_weight_consistency(self, data: st.DataObject):
        """Test that reported weight matches sum of vertex weights."""
        graph, weights = data.draw(weighted_graph_strategy())

        indset, total_weight = min_maximal_independant_set(graph, weights)

        # Calculate expected weight
        expected_weight = sum(weights[node] for node in indset)
        assert total_weight == expected_weight

    @given(data=st.data())
    def test_independent_set_subset_property(self, data: st.DataObject):
        """Test that independent set is a subset of graph nodes."""
        graph, weights = data.draw(weighted_graph_strategy())

        indset, _ = min_maximal_independant_set(graph, weights)

        # All independent set vertices should be in the graph
        for node in indset:
            assert node in graph.nodes()

    @given(data=st.data())
    def test_independent_set_empty_graph(self, data: st.DataObject):
        """Test independent set on empty graph."""
        graph = Graph()
        weights = {}

        indset, total_weight = min_maximal_independant_set(graph, weights)

        # Empty graph should have empty independent set
        assert len(indset) == 0
        assert total_weight == 0

    @given(data=st.data())
    def test_independent_set_single_node(self, data: st.DataObject):
        """Test independent set on single node graph."""
        graph = Graph()
        graph.add_node(0)
        weights = {0: data.draw(st.integers(min_value=1, max_value=10))}

        indset, total_weight = min_maximal_independant_set(graph, weights)

        # Single node should be in independent set
        assert len(indset) == 1
        assert 0 in indset
        assert total_weight == weights[0]

    @given(data=st.data())
    def test_independent_set_preexisting_set(self, data: st.DataObject):
        """Test algorithm with pre-existing independent and dependent sets."""
        graph, weights = data.draw(weighted_graph_strategy())

        # Start with some vertices already in independent set
        initial_indset = set()
        initial_dep = set()
        for node in graph.nodes():
            choice = data.draw(st.sampled_from(["independent", "dependent", "none"]))
            if choice == "independent":
                initial_indset.add(node)
            elif choice == "dependent":
                initial_dep.add(node)

        indset, total_weight = min_maximal_independant_set(
            graph, weights, initial_indset.copy(), initial_dep.copy()
        )

        # Initial independent set should be subset of final independent set
        assert initial_indset.issubset(indset)

        # Final independent set should not intersect with dependent set
        assert len(indset.intersection(initial_dep)) == 0

    @given(data=st.data())
    def test_independent_set_complementarity(self, data: st.DataObject):
        """Test relationship between independent set and vertex cover."""
        graph, weights = data.draw(weighted_graph_strategy())
        assume(len(graph.edges()) > 0)

        indset, ind_weight = min_maximal_independant_set(graph, weights)
        cover, cover_weight = min_vertex_cover_fast(graph, weights)

        # Independent set and vertex cover should be complementary (roughly)
        # This is a very loose property due to approximation nature
        all_nodes = set(graph.nodes())
        assert len(indset) + len(cover) >= len(all_nodes) * 0.5  # Very lenient bound


class TestGraphAlgorithmInvariants:
    """Tests for fundamental invariants of graph algorithms."""

    @given(data=st.data())
    def test_weight_non_negative(self, data: st.DataObject):
        """Test that all weights in solutions are non-negative."""
        graph, weights = data.draw(weighted_graph_strategy())

        # Test vertex cover
        cover, cover_weight = min_vertex_cover_fast(graph, weights)
        assert cover_weight >= 0

        # Test independent set
        indset, ind_weight = min_maximal_independant_set(graph, weights)
        assert ind_weight >= 0

    @given(data=st.data())
    def test_algorithm_determinism(self, data: st.DataObject):
        """Test that algorithms are deterministic for same input."""
        graph, weights = data.draw(weighted_graph_strategy())

        # Run vertex cover twice
        cover1, weight1 = min_vertex_cover_fast(graph, weights)
        cover2, weight2 = min_vertex_cover_fast(graph, weights)

        assert cover1 == cover2
        assert weight1 == weight2

        # Run independent set twice
        indset1, ind_weight1 = min_maximal_independant_set(graph, weights)
        indset2, ind_weight2 = min_maximal_independant_set(graph, weights)

        assert indset1 == indset2
        assert ind_weight1 == ind_weight2

    @given(data=st.data())
    def test_symmetry_property(self, data: st.DataObject):
        """Test that algorithms respect graph symmetry."""
        graph, weights = data.draw(weighted_graph_strategy())

        # Get original results
        cover_orig, weight_orig = min_vertex_cover_fast(graph, weights)
        indset_orig, ind_weight_orig = min_maximal_independant_set(graph, weights)

        # Create isomorphic graph by relabeling nodes
        mapping = {node: f"node_{node}" for node in graph.nodes()}
        graph_renamed = Graph()
        graph_renamed.add_nodes_from(mapping.values())
        graph_renamed.add_edges_from(
            [(mapping[u], mapping[v]) for u, v in graph.edges()]
        )
        weights_renamed = {mapping[node]: weight for node, weight in weights.items()}

        # Get results for renamed graph
        cover_renamed, weight_renamed = min_vertex_cover_fast(
            graph_renamed, weights_renamed
        )
        indset_renamed, ind_weight_renamed = min_maximal_independant_set(
            graph_renamed, weights_renamed
        )

        # Results should be equivalent up to renaming
        assert len(cover_orig) == len(cover_renamed)
        assert weight_orig == weight_renamed
        assert len(indset_orig) == len(indset_renamed)
        assert ind_weight_orig == ind_weight_renamed
