"""Measure the Python odd-cycle-cover oracle before/after and write JSON.

Consumed by ``figures/generate_figures.py`` to draw the Python scaling curve
from real measurements instead of hard-coded numbers. Run with::

    python figures/measure_odd_cycle_cover.py
"""

from __future__ import annotations

import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "experiments"))

import networkx as nx  # noqa: E402

import cover_ai  # noqa: E402
from netlistx.cover import min_odd_cycle_cover as new_odd_cycle_cover  # noqa: E402

SIZES = [(50, 75), (100, 150), (200, 300), (400, 600)]
WEIGHT_SEED = 12345


def make_graph(n: int, m: int) -> tuple[nx.Graph, dict[int, int]]:
    p = min(1.0, (2.0 * m) / (n * (n - 1)))
    ugraph = nx.fast_gnp_random_graph(n, p, seed=42)
    rng = random.Random(WEIGHT_SEED)
    weight = {v: rng.randint(1, 10) for v in ugraph.nodes()}
    return ugraph, weight


def timed(func, *args):
    start = time.perf_counter()
    result = func(*args)
    return result, (time.perf_counter() - start) * 1000.0


def main() -> None:
    out: dict[str, list] = {
        "n": [],
        "before_ms": [],
        "after_ms": [],
        "before_cover": [],
        "after_cover": [],
        "before_cost": [],
        "after_cost": [],
    }
    for n, m in SIZES:
        ugraph, weight = make_graph(n, m)
        (before, cost_before), ms_before = timed(cover_ai.min_odd_cycle_cover, ugraph, weight)
        (after, cost_after), ms_after = timed(new_odd_cycle_cover, ugraph, weight)
        out["n"].append(n)
        out["before_ms"].append(round(ms_before, 4))
        out["after_ms"].append(round(ms_after, 4))
        out["before_cover"].append(len(before))
        out["after_cover"].append(len(after))
        out["before_cost"].append(cost_before)
        out["after_cost"].append(cost_after)
        print(
            f"n={n:>3}: before {ms_before:8.1f} ms ({len(before)},{cost_before})"
            f"  after {ms_after:7.3f} ms ({len(after)},{cost_after})"
        )

    path = os.path.join(HERE, "odd_cycle_cover_timings.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2)
    print("wrote", path)


if __name__ == "__main__":
    main()
