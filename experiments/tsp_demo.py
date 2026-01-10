import random

import matplotlib.pyplot as plt
import networkx as nx


def christofides_tsp(G):
    # 1. Create a Minimum Spanning Tree (MST)
    mst = nx.minimum_spanning_tree(G, weight="weight")

    # 2. Find nodes with odd degrees in the MST
    odd_degree_nodes = [v for v, d in mst.degree() if d % 2 != 0]

    # 3. Find a Minimum Weight Perfect Matching (MWPM) for odd-degree nodes
    # We create a subgraph of the original G containing only odd-degree nodes
    odd_nodes_subgraph = G.subgraph(odd_degree_nodes)
    # We use negative weights because nx.max_weight_matching finds the maximum
    matching = nx.min_weight_matching(odd_nodes_subgraph, weight="weight")

    # 4. Combine MST and Matching to create a Multigraph
    multigraph = nx.MultiGraph(mst)
    multigraph.add_edges_from((u, v, G[u][v]) for u, v in matching)

    # 5. Find an Eulerian Circuit
    eulerian_circuit = list(nx.eulerian_circuit(multigraph))

    # 6. Shortcut the circuit (remove repeated nodes) to get the Hamiltonian Path
    path = []
    visited = set()
    for u, v in eulerian_circuit:
        if u not in visited:
            path.append(u)
            visited.add(u)
    path.append(path[0])  # Close the loop

    return path


# --- Setup and Execution ---
# Create a complete graph with random coordinates (Metric TSP)
num_nodes = 20
G = nx.complete_graph(num_nodes)
pos = {i: (random.uniform(0, 100), random.uniform(0, 100)) for i in range(num_nodes)}

for u, v in G.edges():
    # Euclidean distance
    dist = ((pos[u][0] - pos[v][0]) ** 2 + (pos[u][1] - pos[v][1]) ** 2) ** 0.5
    G[u][v]["weight"] = dist

# Run Algorithm
tsp_path = christofides_tsp(G)

# Visualization
plt.figure(figsize=(8, 6))
nx.draw(G, pos, with_labels=True, node_color="lightblue", edge_color="gray", alpha=0.3)
edgelist = [(tsp_path[i], tsp_path[i + 1]) for i in range(len(tsp_path) - 1)]
nx.draw_networkx_edges(G, pos, edgelist=edgelist, edge_color="red", width=2)
plt.title("Christofides TSP Approximation")
plt.show()

print(f"TSP Path: {tsp_path}")
