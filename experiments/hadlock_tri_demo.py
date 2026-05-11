import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy.spatial import Delaunay

from netlistx.hadlock import solve_hadlock_max_cut, validate_max_cut


def demo_hadlock_tri(num_nodes=100):
    # 1. Generate Random Planar Graph via Delaunay triangulation
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

    # 2. Solve MAX-CUT using Hadlock's algorithm
    max_cut_edges = solve_hadlock_max_cut(G)
    is_bipartite, weight = validate_max_cut(G, max_cut_edges)

    # Excluded edges for visualization
    all_edges = set(tuple(sorted(e)) for e in G.edges())
    excluded_edges_set = all_edges - set(tuple(sorted(e)) for e in max_cut_edges)

    assert is_bipartite is True

    # 3. Visualization
    plt.figure(figsize=(10, 8))
    pos = {i: points[i] for i in range(num_nodes)}

    # Color nodes by bipartition
    node_color = "black"
    if is_bipartite:
        cut_graph = nx.Graph()
        cut_graph.add_edges_from(max_cut_edges)
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
        G, pos, edgelist=list(max_cut_edges), edge_color="red", width=1.5, alpha=0.6
    )
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=list(excluded_edges_set),
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
    demo_hadlock_tri(100)
