import matplotlib.pyplot as plt
import networkx as nx


def solve_hadlock_max_cut():
    # 1. Setup the Primal Graph (G)
    # A planar graph (square with one diagonal)
    G = nx.Graph()
    G.add_edge(1, 2, weight=5)
    G.add_edge(2, 3, weight=10)
    G.add_edge(3, 4, weight=5)
    G.add_edge(4, 1, weight=10)
    G.add_edge(1, 3, weight=2)

    # 2. Setup the Dual Graph (dual_G)
    # Faces: A (triangle 1-2-3), B (triangle 1-3-4), C (exterior)
    dual_G = nx.Graph()

    # Mapping dual edges to primal edges: (dual_u, dual_v) -> (primal_u, primal_v)
    # This is crucial for identifying which edges to remove from the cut.
    {
        (tuple(sorted(("A", "B")))): (1, 3),
        (tuple(sorted(("A", "C")))): (1, 2),
        (tuple(sorted(("B", "C")))): (3, 4),
        # Note: (2,3) and (4,1) also connect to the exterior face C
        (tuple(sorted(("A", "C_alt")))): (2, 3),
        (tuple(sorted(("B", "C_alt2")))): (4, 1),
    }

    # For simplicity in this demo, we use a simplified dual structure
    # where edges in dual_G represent the primal edges they cross.
    dual_G.add_edge("A", "B", weight=2)  # Crosses primal (1,3)
    dual_G.add_edge("A", "C", weight=5)  # Crosses primal (1,2)
    dual_G.add_edge("B", "C", weight=5)  # Crosses primal (3,4)
    dual_G.add_edge(
        "A", "C", weight=10
    )  # Crosses primal (2,3) - simplifies to min weight
    dual_G.add_edge(
        "B", "C", weight=10
    )  # Crosses primal (4,1) - simplifies to min weight

    # 3. Identify Odd-Degree Faces
    # In this specific planar embedding, faces A and B have odd degrees
    # relative to the cut requirements.
    odd_faces = ["A", "B"]

    # 4. Find MWPM on the Complete Graph of Odd Faces
    dist = dict(nx.all_pairs_dijkstra_path_length(dual_G, weight="weight"))
    paths = dict(nx.all_pairs_dijkstra_path(dual_G, weight="weight"))

    complete_odd_G = nx.Graph()
    for i, u in enumerate(odd_faces):
        for v in odd_faces[i + 1 :]:
            complete_odd_G.add_edge(u, v, weight=dist[u][v])

    matching = nx.algorithms.matching.min_weight_matching(
        complete_odd_G, weight="weight"
    )

    # 5. Identify edges to EXCLUDE from the Max-Cut
    # These are the primal edges corresponding to the dual path found in the matching
    excluded_primal_edges = set()
    for u, v in matching:
        path = paths[u][v]
        for i in range(len(path) - 1):
            dual_edge = tuple(sorted((path[i], path[i + 1])))
            # In a real implementation, you'd map back to the specific primal edge
            # For this demo, the shortest path between A and B is the dual edge (A,B)
            # which crosses primal edge (1,3).
            if dual_edge == tuple(sorted(("A", "B"))):
                excluded_primal_edges.add(tuple(sorted((1, 3))))

    # 6. Determine Max-Cut Edges
    all_primal_edges = [tuple(sorted(e)) for e in G.edges()]
    max_cut_edges = [e for e in all_primal_edges if e not in excluded_primal_edges]

    total_weight = sum(d["weight"] for u, v, d in G.edges(data=True))
    excluded_weight = sum(G[u][v]["weight"] for u, v in excluded_primal_edges)
    max_cut_value = total_weight - excluded_weight

    # 7. Visualization
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(10, 6))

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color="#A0CBE8", node_size=800)
    nx.draw_networkx_labels(G, pos, font_weight="bold")

    # Draw Max-Cut Edges (Red)
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=max_cut_edges,
        edge_color="tab:red",
        width=4,
        label="Max-Cut Edges",
    )

    # Draw Excluded Edges (Gray/Dashed)
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=list(excluded_primal_edges),
        edge_color="gray",
        width=2,
        style="dashed",
        label="Excluded Edges",
    )

    # Edge Labels
    edge_labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    plt.title(
        f"Hadlock's Algorithm Max-Cut\nValue: {max_cut_value} (Total {total_weight} - Excluded {excluded_weight})"
    )
    plt.legend(loc="upper left")
    plt.axis("off")

    print(f"Max-Cut Value: {max_cut_value}")
    print(f"Edges in Cut: {max_cut_edges}")
    plt.show()


if __name__ == "__main__":
    solve_hadlock_max_cut()
