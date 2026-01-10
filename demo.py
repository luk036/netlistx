import random

import matplotlib.pyplot as plt
import networkx as nx

from netlistx.cover_ai import min_cycle_cover, min_vertex_cover


def run_graphical_demo():
    # 1. Setup: Create a graph with cycles and some "dead ends" (bridges)
    G = nx.connected_watts_strogatz_graph(n=12, k=3, p=0.2, seed=42)
    # Add a bridge and a leaf to test biconnected component logic
    G.add_edge(11, 12)

    # Assign random weights to vertices
    weight = {node: random.randint(1, 5) for node in G.nodes()}
    pos = nx.spring_layout(G, seed=42)

    # 2. Run Algorithms
    vc_nodes, vc_cost = min_vertex_cover(G, weight)
    cc_nodes, cc_cost = min_cycle_cover(G, weight)

    # 3. Visualization
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Plot Vertex Cover
    nx.draw(
        G, pos, ax=axes[0], with_labels=True, node_color="lightgrey", edge_color="gray"
    )
    nx.draw_networkx_nodes(
        G, pos, ax=axes[0], nodelist=list(vc_nodes), node_color="salmon"
    )
    axes[0].set_title(f"Min Vertex Cover\nCost: {vc_cost} | Nodes: {len(vc_nodes)}")

    # Plot Cycle Cover
    nx.draw(
        G, pos, ax=axes[1], with_labels=True, node_color="lightgrey", edge_color="gray"
    )
    nx.draw_networkx_nodes(
        G, pos, ax=axes[1], nodelist=list(cc_nodes), node_color="skyblue"
    )
    axes[1].set_title(f"Min Cycle Cover\nCost: {cc_cost} | Nodes: {len(cc_nodes)}")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    run_graphical_demo()
