import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
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
    # 1. Generate Random Planar Graph
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
            G.add_edge(u, v, weight=np.random.randint(1, 10))

    # 2. Construct Dual Graph
    # Nodes in dual_G are indices of the triangles (simplices)
    dual_G = nx.Graph()
    for i, neighbors in enumerate(tri.neighbors):
        for j in neighbors:
            if j != -1:
                # Find shared edge between triangle i and triangle j
                shared = list(set(tri.simplices[i]) & set(tri.simplices[j]))
                if len(shared) == 2:
                    u, v = sorted(shared)
                    dual_G.add_edge(i, j, weight=G[u][v]["weight"], primal=(u, v))

    # 3. Every triangle is an odd cycle (length 3).
    # To make the graph bipartite, we must match ALL these faces.
    odd_faces = list(dual_G.nodes())

    # If we have an odd number of faces, we need to handle this case
    # For Hadlock's algorithm, we should ensure we have an even number
    if len(odd_faces) % 2 != 0:
        # Remove one face to ensure even number for perfect matching
        # This is a heuristic - in practice, more sophisticated approaches exist
        odd_faces = odd_faces[:-1]

    # 4. MWPM on Dual
    # Create a complete graph of odd faces with shortest path distances
    dist = dict(nx.all_pairs_dijkstra_path_length(dual_G, weight="weight"))
    paths = dict(nx.all_pairs_dijkstra_path(dual_G, weight="weight"))

    complete_odd_G = nx.Graph()
    complete_odd_G.add_nodes_from(odd_faces)

    # Add edges between all pairs of odd faces with their shortest path distances
    for i in range(len(odd_faces)):
        for j in range(i + 1, len(odd_faces)):
            u, v = odd_faces[i], odd_faces[j]
            if v in dist[u]:
                complete_odd_G.add_edge(u, v, weight=dist[u][v])

    # Find minimum weight perfect matching
    matching = nx.algorithms.matching.min_weight_matching(
        complete_odd_G, weight="weight"
    )

    # 5. Identify Excluded Edges (Edges that break the odd cycles)
    excluded_edges = set()
    for u, v in matching:
        path = paths[u][v]
        for k in range(len(path) - 1):
            p_edge = dual_G[path[k]][path[k + 1]]["primal"]
            excluded_edges.add(tuple(sorted(p_edge)))

    # 6. Max-Cut Edges
    all_edges = [tuple(sorted(e)) for e in G.edges()]
    max_cut_edges = [e for e in all_edges if e not in excluded_edges]

    # 7. Validation
    is_bipartite, weight = validate_max_cut(G, max_cut_edges)

    assert is_bipartite is True

    # 8. Visualization
    plt.figure(figsize=(10, 8))
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
        f"Planar MAX-CUT (Hadlock)\nBipartite Valid: {is_bipartite} | Cut Weight: {weight}"
    )
    plt.show()

    print(f"Validation: Is the cut subgraph bipartite? {is_bipartite}")
    print(f"Total Cut Weight: {weight}")


if __name__ == "__main__":
    solve_hadlock_refined(100)
