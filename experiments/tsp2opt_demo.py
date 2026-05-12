"""
TSP Demo — 2-Opt refinement on a larger random Euclidean instance.

Demonstrates the improvement from using 2-Opt after the Christofides
initial tour, for a 100-city instance.
"""

import math
import os
import random

import matplotlib

try:
    import tkinter  # noqa: F401
except ImportError:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from netlistx.tsp import (
    calculate_total_distance,
    christofides_tsp,
    solve_christofides_2opt_tsp,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Create a complete graph with random coordinates (Metric TSP)
num_nodes = 100
G = nx.complete_graph(num_nodes)
pos = {i: (random.uniform(0, 100), random.uniform(0, 100)) for i in range(num_nodes)}

for u, v in G.edges():
    dx = pos[u][0] - pos[v][0]
    dy = pos[u][1] - pos[v][1]
    G[u][v]["weight"] = math.sqrt(dx * dx + dy * dy)

# Run Christofides alone
initial_path = christofides_tsp(G)
initial_dist = calculate_total_distance(initial_path, G)

# Run combined solver (Christofides + 2-Opt)
combined_path = solve_christofides_2opt_tsp(G)
combined_dist = calculate_total_distance(combined_path, G)

print(f"Initial Distance (Christofides):        {initial_dist:.2f}")
print(f"Refined Distance (Christofides + 2-Opt): {combined_dist:.2f}")
print(f"Improvement:                            {initial_dist - combined_dist:.2f}")

# Visualization of refined path
plt.figure(figsize=(8, 6))
nx.draw(G, pos, with_labels=True, node_color="lightgreen", edge_color="gray", alpha=0.2)
edgelist = [
    (combined_path[i], combined_path[i + 1]) for i in range(len(combined_path) - 1)
]
nx.draw_networkx_edges(G, pos, edgelist=edgelist, edge_color="blue", width=2)
plt.title(
    f"Refined TSP (Christofides + 2-Opt, Improvement: {initial_dist - combined_dist:.2f})"
)
plt.tight_layout()
plt.savefig(os.path.join(SCRIPT_DIR, "tsp2opt_demo_n100.svg"), format="svg")
plt.show()
