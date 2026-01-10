import random

import matplotlib.pyplot as plt
import networkx as nx


def calculate_total_distance(path, G):
    """Calculates the total length of a path."""
    distance = 0
    for i in range(len(path) - 1):
        distance += G[path[i]][path[i + 1]]["weight"]
    return distance


def two_opt(path, G):
    """Refines the TSP path using the 2-opt heuristic."""
    best_path = path
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best_path) - 2):
            for j in range(i + 1, len(best_path)):
                if j - i == 1:
                    continue  # Skip adjacent edges

                # Current edges: (i-1, i) and (j-1, j)
                # Potential new edges: (i-1, j-1) and (i, j)
                # We reverse the segment between i and j-1
                new_path = best_path[:i] + best_path[i:j][::-1] + best_path[j:]

                if calculate_total_distance(new_path, G) < calculate_total_distance(
                    best_path, G
                ):
                    best_path = new_path
                    improved = True
        path = best_path
    return best_path


def christofides_tsp(G):
    # Phase 1-4: Standard Christofides (MST -> Matching -> Multigraph -> Euler)
    mst = nx.minimum_spanning_tree(G, weight="weight")
    odd_degree_nodes = [v for v, d in mst.degree() if d % 2 != 0]
    odd_nodes_subgraph = G.subgraph(odd_degree_nodes)
    matching = nx.min_weight_matching(odd_nodes_subgraph, weight="weight")

    multigraph = nx.MultiGraph(mst)
    multigraph.add_edges_from((u, v, G[u][v]) for u, v in matching)

    eulerian_circuit = list(nx.eulerian_circuit(multigraph))

    # Phase 5: Shortcut to Hamiltonian Path
    path = []
    visited = set()
    for u, v in eulerian_circuit:
        if u not in visited:
            path.append(u)
            visited.add(u)
    path.append(path[0])
    return path


# --- Setup ---
num_nodes = 100
G = nx.complete_graph(num_nodes)
pos = {i: (random.uniform(0, 100), random.uniform(0, 100)) for i in range(num_nodes)}

for u, v in G.edges():
    dist = ((pos[u][0] - pos[v][0]) ** 2 + (pos[u][1] - pos[v][1]) ** 2) ** 0.5
    G[u][v]["weight"] = dist

# Run Christofides
initial_path = christofides_tsp(G)
initial_dist = calculate_total_distance(initial_path, G)

# Refine with 2-opt
refined_path = two_opt(initial_path, G)
refined_dist = calculate_total_distance(refined_path, G)

print(f"Initial Distance (Christofides): {initial_dist:.2f}")
print(f"Refined Distance (After 2-opt): {refined_dist:.2f}")

# Visualization of refined path
plt.figure(figsize=(8, 6))
nx.draw(G, pos, with_labels=True, node_color="lightgreen", edge_color="gray", alpha=0.2)
edgelist = [
    (refined_path[i], refined_path[i + 1]) for i in range(len(refined_path) - 1)
]
nx.draw_networkx_edges(G, pos, edgelist=edgelist, edge_color="blue", width=2)
plt.title(f"Refined TSP (2-opt Improvement: {initial_dist - refined_dist:.2f})")
plt.show()
