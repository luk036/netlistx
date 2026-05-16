"""
GPU-Accelerated Randomized Vertex Cover using Pitt's Algorithm

Runs multiple independent Pitt trials in parallel on the GPU via Numba CUDA.
Each CUDA thread executes one complete Pitt trial (edge iteration + random
vertex selection). After all trials complete, the best (lowest cost) cover
is returned.

This Monte Carlo approach exploits GPU parallelism by making each trial
independent, requiring no inter-thread synchronization during execution.

Reference:
    L. Pitt, "A Simple Probabilistic Approximation Algorithm for Vertex Cover,"
    Technical Report, Yale University, 1985.
"""

import math
import random as _random
from typing import Dict, MutableMapping, Optional, Set, Tuple, Union

import networkx as nx
import numpy as np
from numba import cuda

THREADS_PER_BLOCK = 64


@cuda.jit
def _pitt_kernel(
    edges,
    num_edges,
    weights,
    num_vertices,
    cover_words,
    costs,
    seeds,
):
    """
    CUDA kernel: each thread runs one independent Pitt trial.

    Each thread maintains its cover as a bitmask (uint32 words) stored
    in device memory at its trial index.
    """
    tid = cuda.grid(1)
    if tid >= costs.shape[0]:
        return

    # cover_words.shape[1]
    seed = seeds[tid]

    for i in range(num_edges):
        u = edges[i, 0]
        v = edges[i, 1]

        u_word = u >> 5
        v_word = v >> 5
        u_bit = 1 << (u & 31)
        v_bit = 1 << (v & 31)

        u_sel = (cover_words[tid, u_word] & u_bit) != 0
        v_sel = (cover_words[tid, v_word] & v_bit) != 0

        if not u_sel and not v_sel:
            # LCG random number generator (per-thread state)
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            rand_val = seed / 2147483648.0

            w_u = weights[u]
            w_v = weights[v]
            threshold = w_v / (w_u + w_v)

            if rand_val < threshold:
                cover_words[tid, u_word] |= u_bit
            else:
                cover_words[tid, v_word] |= v_bit

    # Compute cost
    cost = 0
    for vi in range(num_vertices):
        vi_word = vi >> 5
        vi_bit = 1 << (vi & 31)
        if (cover_words[tid, vi_word] & vi_bit) != 0:
            cost += weights[vi]

    costs[tid] = cost


def rand_vertex_cover_gpu(
    ugraph: nx.Graph,
    weight: MutableMapping,
    coverset: Optional[Set] = None,
    num_trials: int = 1024,
    seed: Optional[int] = None,
) -> Tuple[Set, Union[int, float]]:
    """
    Find a minimum weighted vertex cover using GPU-accelerated Pitt's algorithm.

    Runs ``num_trials`` independent randomized Pitt trials in parallel on the
    GPU and returns the cover with the lowest total weight.

    :param ugraph: The input undirected graph.
    :type ugraph: nx.Graph
    :param weight: A mapping from vertices to their weights.
    :type weight: MutableMapping
    :param coverset: Optional initial vertex cover (default: empty set).
    :type coverset: Optional[Set]
    :param num_trials: Number of parallel Monte Carlo trials (default: 1024).
    :type num_trials: int
    :param seed: Random seed for reproducible results (default: None).
    :type seed: Optional[int]

    :return: A tuple of (best vertex cover set, total weight).
    :rtype: Tuple[Set, Union[int, float]]

    Examples:
        >>> ugraph = nx.Graph()
        >>> ugraph.add_edges_from([(0, 1), (0, 2), (1, 2)])
        >>> weight = {0: 1, 1: 1, 2: 1}
        >>> soln, cost = rand_vertex_cover_gpu(ugraph, weight, num_trials=64, seed=42)
        >>> isinstance(soln, set)
        True
        >>> all(u in soln or v in soln for u, v in ugraph.edges())
        True
    """
    if not cuda.is_available():
        raise RuntimeError("No CUDA-capable GPU found")

    if coverset is None:
        coverset = set()

    # Map vertices to consecutive integer indices
    vertices = list(ugraph.nodes())
    n_vertices = len(vertices)
    vertex_to_idx: Dict = {v: i for i, v in enumerate(vertices)}

    # Handle trivial edge cases before launching the kernel
    n_edges = ugraph.number_of_edges()
    if n_edges == 0:
        return set(coverset), sum(weight[v] for v in coverset)

    # Build edge array (n_edges, 2) of int32 — explicit 2D even when empty
    edges_list = [(vertex_to_idx[u], vertex_to_idx[v]) for u, v in ugraph.edges()]

    # Build weight array
    weights_list = [float(weight[v]) for v in vertices]

    edges_np = np.array(edges_list, dtype=np.int32)
    weights_np = np.array(weights_list, dtype=np.float32)

    # Generate seeds for each trial
    rng = _random.Random(seed)
    seeds_np = np.array(
        [rng.randint(0, 2**31 - 1) for _ in range(num_trials)], dtype=np.int32
    )

    # Allocate cover bitmask array: (num_trials, num_words)
    num_words = (n_vertices + 31) // 32
    covers_np = np.zeros((num_trials, num_words), dtype=np.uint32)

    # Apply initial coverset to all trials
    for v in coverset:
        vi = vertex_to_idx[v]
        word = vi >> 5
        bit = 1 << (vi & 31)
        for t in range(num_trials):
            covers_np[t, word] |= bit

    costs_np = np.zeros(num_trials, dtype=np.float32)

    # Copy data to device
    d_edges = cuda.to_device(edges_np)
    d_weights = cuda.to_device(weights_np)
    d_covers = cuda.to_device(covers_np)
    d_costs = cuda.to_device(costs_np)
    d_seeds = cuda.to_device(seeds_np)

    # Launch kernel
    blocks = int(math.ceil(num_trials / THREADS_PER_BLOCK))
    _pitt_kernel[blocks, THREADS_PER_BLOCK](
        d_edges,
        n_edges,
        d_weights,
        n_vertices,
        d_covers,
        d_costs,
        d_seeds,
    )
    cuda.synchronize()

    # Copy results back
    d_costs.copy_to_host(costs_np)
    d_covers.copy_to_host(covers_np)

    # Find best trial
    best_idx = int(np.argmin(costs_np))
    best_cost = float(costs_np[best_idx])

    # Extract best cover set
    best_mask = covers_np[best_idx]
    soln: Set = set()
    for vi in range(n_vertices):
        if (best_mask[vi >> 5] >> (vi & 31)) & 1:
            soln.add(vertices[vi])

    return soln, best_cost
