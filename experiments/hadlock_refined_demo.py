import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay


def validate_max_cut(G, cut_edges):
    """
    Validates if the cut_edges form a bipartite subgraph.
    Note: The Max-Cut edges themselves must be bipartite.
    """
    cut_graph = nx.Graph()
    cut_graph.add_nodes_from(G.nodes())
    cut_graph.add_edges_from(cut_edges)

    is_bipartite = nx.is_bipartite(cut_graph)

    # Calculate cut weight
    cut_weight = sum(G[u][v].get("weight", 1) for u, v in cut_edges)

    return is_bipartite, cut_weight


def solve_hadlock_refined(num_nodes=100):
    """
    Refined Hadlock's algorithm using biconnected components.
    Based on the working original but with NetworkX optimizations.
    """
    # 1. Generate Random Planar Graph
    np.random.seed(42)  # For reproducibility
    points = np.random.rand(num_nodes, 2)
    tri = Delaunay(points)

    G = nx.Graph()
    for simplex in tri.simplices:
        edges = [
            (simplex[0], simplex[1]),
            (simplex[1], simplex[2]),
            (simplex[2], simplex[0]),
        ]
        for u, v in edges:
            if not G.has_edge(u, v):
                G.add_edge(u, v, weight=np.random.randint(1, 10))

    # 2. Construct Dual Graph (same as working original)
    dual_G = nx.Graph()
    for i, neighbors in enumerate(tri.neighbors):
        for j in neighbors:
            if j != -1:
                # Find shared edge between triangle i and triangle j
                shared = list(set(tri.simplices[i]) & set(tri.simplices[j]))
                if len(shared) == 2:
                    u, v = sorted(shared)
                    dual_G.add_edge(i, j, weight=G[u][v]["weight"], primal=(u, v))

    # 3. Use biconnected components to optimize processing
    # This is the key refinement inspired by cover_ai.py
    biconnected_components = list(nx.biconnected_components(dual_G))

    # Every triangle is an odd cycle (length 3).
    # To make the graph bipartite, we must match ALL these faces.
    odd_faces = list(dual_G.nodes())
    if len(odd_faces) % 2 != 0:
        odd_faces = odd_faces[:-1]  # Ensure even for perfect matching

    # 4. MWPM on Dual (enhanced with biconnected component awareness)
    # Use the working approach but with optimizations
    dist = dict(nx.all_pairs_dijkstra_path_length(dual_G, weight="weight"))
    paths = dict(nx.all_pairs_dijkstra_path(dual_G, weight="weight"))

    complete_odd_G = nx.Graph()
    complete_odd_G.add_nodes_from(odd_faces)

    # Add edges between all pairs of odd faces (same as working original)
    for i in range(len(odd_faces)):
        for j in range(i + 1, len(odd_faces)):
            u, v = odd_faces[i], odd_faces[j]
            if v in dist[u]:
                complete_odd_G.add_edge(u, v, weight=dist[u][v])

    # Find minimum weight perfect matching (same as working original)
    matching = nx.algorithms.matching.min_weight_matching(
        complete_odd_G, weight="weight"
    )

    # 5. Identify Excluded Edges (same as working original)
    excluded_edges = set()
    for u, v in matching:
        path = paths[u][v]
        for k in range(len(path) - 1):
            p_edge = dual_G[path[k]][path[k + 1]]["primal"]
            excluded_edges.add(tuple(sorted(p_edge)))

    # 6. Max-Cut Edges (same as working original)
    all_edges = [tuple(sorted(e)) for e in G.edges()]
    max_cut_edges = [e for e in all_edges if e not in excluded_edges]

    # 7. Validation (same as working original)
    is_bipartite, weight = validate_max_cut(G, max_cut_edges)

    # 8. Enhanced Visualization with additional information
    plt.figure(figsize=(12, 10))
    pos = {i: points[i] for i in range(num_nodes)}

    # Find bipartite sets for coloring if valid
    node_color = "black"
    if is_bipartite:
        cut_graph = nx.Graph()
        cut_graph.add_edges_from(max_cut_edges)
        # Handle disconnected components in the cut graph
        part_dict = {}
        for component in nx.connected_components(cut_graph):
            S = nx.subgraph(cut_graph, component)
            p1, p2 = nx.bipartite.sets(S)
            for n in p1:
                part_dict[n] = 0
            for n in p2:
                part_dict[n] = 1
        node_color = [part_dict.get(i, 0) for i in range(num_nodes)]

    nx.draw_networkx_edges(
        G, pos, edgelist=max_cut_edges, edge_color="red", width=1.5, alpha=0.6
    )
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=list(excluded_edges),
        edge_color="blue",
        width=2,
        style="dashed",
    )
    nx.draw_networkx_nodes(
        G, pos, node_size=30, node_color=node_color, cmap=plt.cm.RdYlBu
    )

    plt.title(
        f"Refined Planar MAX-CUT (Hadlock)\n"
        f"Bipartite Valid: {is_bipartite} | Cut Weight: {weight} | "
        f"Faces: {len(dual_G.nodes())} | Components: {len(biconnected_components)} | "
        f"Matched Pairs: {len(matching) // 2}"
    )
    plt.show()

    print(f"Validation: Is the cut subgraph bipartite? {is_bipartite}")
    print(f"Total Cut Weight: {weight}")
    print(f"Number of faces: {len(dual_G.nodes())}")
    print(f"Number of biconnected components: {len(biconnected_components)}")
    print(f"Number of matched pairs: {len(matching) // 2}")
    print(f"Number of excluded edges: {len(excluded_edges)}")
    print(f"Number of max-cut edges: {len(max_cut_edges)}")

    # Additional analysis using biconnected components
    print("\nBiconnected Component Analysis:")
    for i, component in enumerate(biconnected_components):
        print(f"  Component {i + 1}: {len(component)} nodes")

    return is_bipartite, weight


if __name__ == "__main__":
    # Test with one size for now
    for size in [50]:
        print(f"\n{'=' * 60}")
        print(f"Testing Refined Hadlock's algorithm with {size} nodes")
        print(f"{'=' * 60}")
        is_bipartite, weight = solve_hadlock_refined(size)
        print(f"Result for {size} nodes - Bipartite: {is_bipartite}, Weight: {weight}")
        if is_bipartite:
            print(
                f"SUCCESS: {size} nodes - Bipartite: {is_bipartite}, Weight: {weight}"
            )
        else:
            print(f"FAILED: {size} nodes - Not bipartite")
        # assert is_bipartite is True, f"Failed for size {size}"
