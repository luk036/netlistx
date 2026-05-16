"""
Demo comparing different vertex cover algorithms on a random graph.

Compares:
  - min_vertex_cover     (primal-dual 2-approx)
  - min_vertex_cover_fast (greedy, no post-processing)
  - rand_vertex_cover    (Pitt's randomized, single trial)
  - rand_vertex_cover_gpu (GPU-accelerated, many trials)
"""

import random
from dataclasses import dataclass
from typing import Dict, List

import matplotlib.pyplot as plt
import networkx as nx

from netlistx.cover import min_vertex_cover
from netlistx.graph_algo import min_vertex_cover_fast
from netlistx.rand_cover import rand_vertex_cover

try:
    from netlistx.rand_cover_gpu import rand_vertex_cover_gpu

    HAS_CUDA = True
except (ImportError, RuntimeError):
    HAS_CUDA = False


@dataclass
class Result:
    name: str
    cover: set
    cost: float
    color: str


def run_algorithms(G: nx.Graph, weight: Dict) -> List[Result]:
    """Run all vertex cover algorithms and return results."""
    results = []

    # 1. Primal-Dual 2-Approximation
    vc_nodes, vc_cost = min_vertex_cover(G, weight)
    results.append(Result("Primal-Dual", vc_nodes, vc_cost, "salmon"))

    # 2. Fast Greedy (no post-processing)
    try:
        fg_nodes, fg_cost = min_vertex_cover_fast(G, weight)
        results.append(Result("Fast Greedy", fg_nodes, fg_cost, "gold"))
    except Exception:
        pass

    # 3. Pitt's Randomized (single trial)
    for seed in [42, 123, 256]:
        rt_nodes, rt_cost = rand_vertex_cover(G, weight, seed=seed)
        label = f"Pitt (seed={seed})"
        results.append(Result(label, rt_nodes, rt_cost, "skyblue"))

    # 4. Pitt's Randomized (multiple trials, pick best)
    best_cost = float("inf")
    best_cover = set()
    for s in range(20):
        c, cost = rand_vertex_cover(G, weight, seed=s)
        if cost < best_cost:
            best_cost = cost
            best_cover = c
    results.append(Result("Pitt best-of-20", best_cover, best_cost, "mediumseagreen"))

    # 5. GPU-Accelerated (if available)
    if HAS_CUDA:
        try:
            gc_nodes, gc_cost = rand_vertex_cover_gpu(
                G, weight, num_trials=512, seed=42
            )
            results.append(Result("GPU (512 trials)", gc_nodes, gc_cost, "violet"))
        except Exception:
            pass

    return results


def print_comparison(results: List[Result], optimal_known: bool = False) -> None:
    """Print a formatted comparison table."""
    print("=" * 70)
    print(f"{'Algorithm':<22} {'Cost':>8} {'|Cover|':>8} {'Color':<12}")
    print("-" * 70)
    for r in results:
        print(f"{r.name:<22} {r.cost:>8.1f} {len(r.cover):>8} {r.color:<12}")
    print("=" * 70)

    best = min(results, key=lambda r: r.cost)
    print(f"*** Best algorithm: {best.name} (cost={best.cost})")


def plot_results(G: nx.Graph, pos: Dict, results: List[Result], weight: Dict) -> None:
    """Visualize each algorithm's cover in a grid of subplots."""
    n = len(results)
    cols = 3
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    axes_flat = axes.flatten() if rows > 1 else [axes] if cols == 1 else axes

    for i, r in enumerate(results):
        ax = axes_flat[i]
        nx.draw(
            G,
            pos,
            ax=ax,
            with_labels=True,
            node_color="lightgrey",
            edge_color="gray",
            node_size=200,
            font_size=8,
        )
        nx.draw_networkx_nodes(
            G, pos, ax=ax, nodelist=list(r.cover), node_color=r.color, node_size=200
        )
        # Annotate weights on nodes
        labels = {n: f"{n}\n(w={weight[n]})" for n in G.nodes()}
        nx.draw_networkx_labels(G, pos, ax=ax, labels=labels, font_size=6)
        ax.set_title(
            f"{r.name}\nCost={r.cost}, |Cover|={len(r.cover)}",
            fontsize=10,
        )

    # Hide unused subplots
    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].set_visible(False)

    plt.tight_layout()
    plt.show()


def main():
    # --- Setup ---
    G = nx.connected_watts_strogatz_graph(n=15, k=3, p=0.3, seed=42)
    G.add_edge(3, 7)
    G.add_edge(10, 12)

    weight = {node: random.randint(1, 5) for node in G.nodes()}
    pos = nx.spring_layout(G, seed=42)

    print("=" * 70)
    print("  Vertex Cover Algorithm Comparison Demo")
    print("=" * 70)
    print(f"  Graph: |V|={G.number_of_nodes()}, |E|={G.number_of_edges()}")
    print(f"  Weights: {dict(sorted(weight.items()))}")
    print()

    # --- Run ---
    results = run_algorithms(G, weight)

    # --- Print ---
    print_comparison(results)

    # --- Plot ---
    print("\n[Plot] Displaying visualization...")
    plot_results(G, pos, results, weight)


if __name__ == "__main__":
    main()
