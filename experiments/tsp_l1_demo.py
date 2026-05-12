"""
TSP L1 Demo — Christofides + 2-Opt on Manhattan (L1) metric instances.

Demonstrates that the same algorithms work identically with Manhattan
distance instead of Euclidean (both satisfy the triangle inequality).
"""

import os

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
    make_l1_graph,
    solve_christofides_2opt_tsp,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Create a complete graph with L1 (Manhattan) metric
num_nodes = 20
G, pos = make_l1_graph(num_nodes, seed=42)

# Run algorithms
tsp_path_initial = christofides_tsp(G)
tsp_path_refined = solve_christofides_2opt_tsp(G)

dist_initial = calculate_total_distance(tsp_path_initial, G)
dist_refined = calculate_total_distance(tsp_path_refined, G)

# Print comparison
print(f"L1 Initial Distance (Christofides):        {dist_initial:.2f}")
print(f"L1 Refined Distance (Christofides+2-Opt):  {dist_refined:.2f}")
print(f"Improvement:                               {dist_initial - dist_refined:.2f}")

# Visualization
plt.figure(figsize=(8, 6))
nx.draw(G, pos, with_labels=True, node_color="lightyellow", edge_color="gray", alpha=0.3)

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

plt.title(
    f"L1 Manhattan — Christofides (red, {dist_initial:.1f})"
    f" → +2-Opt (blue, {dist_refined:.1f})"
)
plt.tight_layout()
plt.savefig(os.path.join(SCRIPT_DIR, "tsp_l1_demo_n20.svg"), format="svg")
plt.show()
