import random

import matplotlib.pyplot as plt
import networkx as nx

from netlistx.hadlock import solve_hadlock_max_cut, validate_max_cut


def demo_hadlock_grid(grid_size=10):
    # 1. Create a Primal Grid Graph
    G = nx.grid_2d_graph(grid_size, grid_size)
    for u, v in G.edges():
        G[u][v]["weight"] = random.randint(1, 20)

    # 2. Solve MAX-CUT using Hadlock's algorithm
    max_cut_edges = solve_hadlock_max_cut(G)
    is_valid, cut_weight = validate_max_cut(G, max_cut_edges)

    # Grids are bipartite → all edges land in the max cut.
    # For a more interesting demo, uncomment the triangulation below.
    excluded_edges = set(tuple(sorted(e)) for e in G.edges()) - set(
        tuple(sorted(e)) for e in max_cut_edges
    )

    # 3. Visualization
    plt.figure(figsize=(12, 10))
    pos = {node: node for node in G.nodes()}

    # Draw excluded edges (should be empty for bipartite grid)
    if excluded_edges:
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=list(excluded_edges),
            edge_color="gray",
            width=1,
            style="dashed",
            alpha=0.5,
        )

    # Draw Max-Cut edges
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=list(max_cut_edges),
        edge_color="red",
        width=2,
        label="Max-Cut Edges",
    )

    nx.draw_networkx_nodes(G, pos, node_size=20, node_color="black")

    plt.title(
        f"Hadlock's Algorithm on {grid_size}x{grid_size} Grid\n"
        f"Bipartite → all edges in cut (weight={cut_weight})"
    )
    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    demo_hadlock_grid(10)
