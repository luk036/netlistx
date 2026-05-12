"""
TSP Demo — Christofides + 2-Opt on random Euclidean instances.

This demo shows both the Christofides initial tour and the 2-Opt refined tour,
with a side-by-side comparison of distances.
"""

import math
import os
import random

import matplotlib

try:
    import tkinter  # noqa: F401  # test for display
except ImportError:
    matplotlib.use("Agg")  # headless fallback
import matplotlib.pyplot as plt
import networkx as nx

from netlistx.tsp import (
    calculate_total_distance,
    christofides_tsp,
    solve_christofides_2opt_tsp,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Create a complete graph with random coordinates (Metric TSP)
num_nodes = 20
G = nx.complete_graph(num_nodes)
pos = {i: (random.uniform(0, 100), random.uniform(0, 100)) for i in range(num_nodes)}

for u, v in G.edges():
    dx = pos[u][0] - pos[v][0]
    dy = pos[u][1] - pos[v][1]
    G[u][v]["weight"] = math.sqrt(dx * dx + dy * dy)

# Run algorithms
tsp_path_initial = christofides_tsp(G)
tsp_path_refined = solve_christofides_2opt_tsp(G)

dist_initial = calculate_total_distance(tsp_path_initial, G)
dist_refined = calculate_total_distance(tsp_path_refined, G)

# Print comparison
print(f"Initial Distance (Christofides):  {dist_initial:.2f}")
print(f"Refined Distance (Christofides+2-Opt): {dist_refined:.2f}")
print(f"Improvement:                       {dist_initial - dist_refined:.2f}")

# Visualization
plt.figure(figsize=(8, 6))
nx.draw(G, pos, with_labels=True, node_color="lightblue", edge_color="gray", alpha=0.3)

edgelist_initial = [
    (tsp_path_initial[i], tsp_path_initial[i + 1])
    for i in range(len(tsp_path_initial) - 1)
]
nx.draw_networkx_edges(
    G, pos, edgelist=edgelist_initial, edge_color="red", width=2, alpha=0.5
)

edgelist_refined = [
    (tsp_path_refined[i], tsp_path_refined[i + 1])
    for i in range(len(tsp_path_refined) - 1)
]
nx.draw_networkx_edges(
    G, pos, edgelist=edgelist_refined, edge_color="blue", width=2, alpha=0.8
)

plt.title(f"Christofides (red, {dist_initial:.1f}) → +2-Opt (blue, {dist_refined:.1f})")
plt.tight_layout()
plt.savefig(os.path.join(SCRIPT_DIR, "tsp_demo_n20.svg"), format="svg")
plt.show()
