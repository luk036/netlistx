import matplotlib.pyplot as plt
import networkx as nx

from netlistx.hadlock import solve_hadlock_max_cut, validate_max_cut


def demo():
    # 1. Setup the Primal Graph (G)
    # A planar graph (square with one diagonal)
    G = nx.Graph()
    G.add_edge(1, 2, weight=5)
    G.add_edge(2, 3, weight=10)
    G.add_edge(3, 4, weight=5)
    G.add_edge(4, 1, weight=10)
    G.add_edge(1, 3, weight=2)

    # 2. Solve MAX-CUT using Hadlock's algorithm
    max_cut_edges = solve_hadlock_max_cut(G)
    is_valid, max_cut_value = validate_max_cut(G, max_cut_edges)

    # Compute excluded edges & total weight for display
    all_edges = set(tuple(sorted(e)) for e in G.edges())
    excluded_edges = all_edges - set(tuple(sorted(e)) for e in max_cut_edges)
    total_weight = sum(d["weight"] for _, _, d in G.edges(data=True))

    # 3. Visualization
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(10, 6))

    nx.draw_networkx_nodes(G, pos, node_color="#A0CBE8", node_size=800)
    nx.draw_networkx_labels(G, pos, font_weight="bold")

    # Draw Max-Cut Edges (Red)
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=list(max_cut_edges),
        edge_color="tab:red",
        width=4,
        label="Max-Cut Edges",
    )

    # Draw Excluded Edges (Gray/Dashed)
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=list(excluded_edges),
        edge_color="gray",
        width=2,
        style="dashed",
        label="Excluded Edges",
    )

    # Edge Labels
    edge_labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    plt.title(
        f"Hadlock's Algorithm Max-Cut\n"
        f"Value: {max_cut_value} (Total {total_weight})"
    )
    plt.legend(loc="upper left")
    plt.axis("off")

    print(f"Max-Cut Value: {max_cut_value}")
    print(f"Edges in Cut: {max_cut_edges}")
    print(f"Bipartite valid: {is_valid}")
    plt.show()


if __name__ == "__main__":
    demo()
