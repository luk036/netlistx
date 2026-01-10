import random

import matplotlib.pyplot as plt
import networkx as nx


def solve_hadlock_large_demo(grid_size=10):
    # 1. Create a Primal Grid Graph (100 nodes)
    G = nx.grid_2d_graph(grid_size, grid_size)
    for u, v in G.edges():
        G[u][v]["weight"] = random.randint(1, 20)

    # 2. Construct the Dual Graph
    # For a grid, faces are (i, j) where 0 <= i, j < grid_size - 1
    dual_G = nx.Graph()

    # Map dual nodes to the primal edges they cross
    # Dual node (i, j) represents the face with corners (i,j), (i+1,j), (i,j+1), (i+1,j+1)
    for r in range(grid_size - 1):
        for c in range(grid_size - 1):
            curr_face = (r, c)
            # Right neighbor face
            if c < grid_size - 2:
                primal_edge = ((r, c + 1), (r + 1, c + 1))
                dual_G.add_edge(
                    curr_face,
                    (r, c + 1),
                    weight=G[primal_edge[0]][primal_edge[1]]["weight"],
                    primal=primal_edge,
                )
            # Bottom neighbor face
            if r < grid_size - 2:
                primal_edge = ((r + 1, c), (r + 1, c + 1))
                dual_G.add_edge(
                    curr_face,
                    (r + 1, c),
                    weight=G[primal_edge[0]][primal_edge[1]]["weight"],
                    primal=primal_edge,
                )

    # 3. Identify "Odd Faces"
    # In a real MAX-CUT, we want to match faces to minimize excluded edges.
    # To demonstrate the matching, we pick a subset of faces to be "odd".
    all_faces = list(dual_G.nodes())
    odd_faces = random.sample(all_faces, 10)  # Picking 10 random faces to match

    # 4. MWPM on Odd Faces
    dist = dict(nx.all_pairs_dijkstra_path_length(dual_G, weight="weight"))
    paths = dict(nx.all_pairs_dijkstra_path(dual_G, weight="weight"))

    complete_odd_G = nx.Graph()
    nodes = list(odd_faces)
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            u, v = nodes[i], nodes[j]
            complete_odd_G.add_edge(u, v, weight=dist[u][v])

    matching = nx.algorithms.matching.min_weight_matching(
        complete_odd_G, weight="weight"
    )

    # 5. Extract Excluded Edges from the matching paths
    excluded_edges = set()
    for u, v in matching:
        path = paths[u][v]
        for k in range(len(path) - 1):
            tuple(sorted((path[k], path[k + 1])))
            e_primal = dual_G[path[k]][path[k + 1]]["primal"]
            excluded_edges.add(tuple(sorted(e_primal)))

    # 6. Separate Edges for Visualization
    all_edges = [tuple(sorted(e)) for e in G.edges()]
    max_cut_edges = [e for e in all_edges if e not in excluded_edges]

    # 7. Visualization
    plt.figure(figsize=(12, 10))
    pos = {node: node for node in G.nodes()}  # Grid layout

    # Draw non-cut edges (light/dashed)
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=list(excluded_edges),
        edge_color="gray",
        width=1,
        style="dashed",
        alpha=0.5,
    )

    # Draw Max-Cut edges (Red/Solid)
    nx.draw_networkx_edges(
        G, pos, edgelist=max_cut_edges, edge_color="red", width=2, label="Max-Cut Edges"
    )

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=20, node_color="black")

    plt.title(
        f"Hadlock's Algorithm on {grid_size}x{grid_size} Grid\nRed = Max Cut, Gray = Excluded Paths"
    )
    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    solve_hadlock_large_demo(10)
