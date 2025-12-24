import matplotlib.pyplot as plt
import networkx as nx
import random
from matplotlib.animation import FuncAnimation
from netlistx.cover_ai import _generic_bfs_cycle, _construct_cycle


def animate_pd_algorithm(ugraph, algorithm_type="vertex_cover"):
    # Setup graph and weights
    pos = nx.spring_layout(ugraph, seed=42)
    weights = {node: random.randint(1, 5) for node in ugraph.nodes()}

    # State tracking
    soln = set()
    added_order = []
    history = []  # To store (current_soln, stage_name, highlight_element)

    # 1. Selection Phase Simulation
    if algorithm_type == "vertex_cover":
        for u, v in ugraph.edges():
            if u not in soln and v not in soln:
                # Find min weight vertex in the violating edge (simplified PD)
                pick = u if weights[u] <= weights[v] else v
                soln.add(pick)
                added_order.append(pick)
                history.append((set(soln), "Selection: Edge Cover", (u, v)))
    else:  # cycle_cover

        def find_violations():
            for info, p, c in _generic_bfs_cycle(ugraph, soln):
                return _construct_cycle(info, p, c)
            return None

        while True:
            S = find_violations()
            if not S:
                break
            pick = min(S, key=lambda v: weights[v])
            soln.add(pick)
            added_order.append(pick)
            history.append((set(soln), "Selection: Cycle Cover", list(S)))

    # 2. Pruning Phase Simulation (Reverse-Delete)
    current_soln = set(soln)
    for vtx in reversed(added_order):
        current_soln.remove(vtx)

        # Check if still covered
        still_covered = True
        if algorithm_type == "vertex_cover":
            if any(
                u not in current_soln and v not in current_soln
                for u, v in ugraph.edges()
            ):
                still_covered = False
        else:
            for _ in _generic_bfs_cycle(ugraph, current_soln):
                still_covered = False
                break

        if not still_covered:
            current_soln.add(vtx)
            history.append((set(current_soln), "Pruning: Keep Essential", vtx))
        else:
            history.append((set(current_soln), "Pruning: Remove Redundant", vtx))

    # Animation Setup
    fig, ax = plt.subplots(figsize=(10, 7))

    def update(frame):
        ax.clear()
        nodes, stage, highlight = history[frame]

        # Draw base graph
        nx.draw_networkx_edges(ugraph, pos, ax=ax, edge_color="gray", alpha=0.5)

        # Highlight violations being addressed
        if stage.startswith("Selection") and highlight:
            if isinstance(highlight, tuple):  # Edge
                nx.draw_networkx_edges(
                    ugraph, pos, edgelist=[highlight], edge_color="red", width=3
                )
            else:  # Cycle/Set
                nx.draw_networkx_nodes(
                    ugraph, pos, nodelist=highlight, node_color="yellow", node_size=600
                )

        # Draw current solution nodes
        nx.draw_networkx_nodes(
            ugraph, pos, ax=ax, node_color="lightgrey", node_size=500
        )
        nx.draw_networkx_nodes(
            ugraph, pos, nodelist=list(nodes), node_color="orange", node_size=500
        )
        nx.draw_networkx_labels(ugraph, pos, ax=ax)

        ax.set_title(f"Algorithm: {algorithm_type}\nPhase: {stage}")

    ani = FuncAnimation(fig, update, frames=len(history), repeat=False, interval=1000)
    plt.show()


if __name__ == "__main__":
    # Test with a graph containing cycles and bridges
    G = nx.Graph([(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (5, 3)])
    animate_pd_algorithm(G, algorithm_type="cycle_cover")
