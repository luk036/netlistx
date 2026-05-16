"""
TSP L1 Demo — 2-Opt refinement on a larger Manhattan (L1) metric instance.

Shows the Christofides + 2-Opt combination scaling to 100 cities with
Manhattan distance.
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
num_nodes = 100
G, pos = make_l1_graph(num_nodes, seed=42)

# Run Christofides alone
initial_path = christofides_tsp(G)
initial_dist = calculate_total_distance(initial_path, G)

# Run combined solver (Christofides + 2-Opt)
combined_path = solve_christofides_2opt_tsp(G)
combined_dist = calculate_total_distance(combined_path, G)

print(f"L1 Initial Distance (Christofides):        {initial_dist:.2f}")
print(f"L1 Refined Distance (Christofides + 2-Opt): {combined_dist:.2f}")
print(f"Improvement:                               {initial_dist - combined_dist:.2f}")

# Visualization of refined path
plt.figure(figsize=(8, 6))
nx.draw(
    G, pos, with_labels=True, node_color="lightyellow", edge_color="gray", alpha=0.2
)
edgelist = [
    (combined_path[i], combined_path[i + 1]) for i in range(len(combined_path) - 1)
]
nx.draw_networkx_edges(G, pos, edgelist=edgelist, edge_color="blue", width=2)
plt.title(
    f"L1 Manhattan (n=100): Christofides + 2-Opt, "
    f"Improvement: {initial_dist - combined_dist:.2f}"
)
plt.tight_layout()
plt.savefig(os.path.join(SCRIPT_DIR, "tsp_l1_n100_demo.svg"), format="svg")
plt.show()
