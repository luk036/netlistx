"""
Traveling Salesman Problem (TSP) Algorithms

This module implements approximation algorithms for the Metric TSP, including
the Christofides algorithm (3/2-approximation) and the 2-Opt local search
heuristic for refinement.

The main entry point is :func:`solve_christofides_2opt_tsp`, which runs
Christofides to obtain an initial tour and then refines it with 2-Opt.

Metric TSP
    A complete graph :math:`G = (V, E)` with edge weights :math:`w_{ij}`
    satisfying the triangle inequality:

    .. math::

        w_{ik} \\le w_{ij} + w_{jk} \\quad \\forall i,j,k \\in V

Christofides Algorithm (1976)
    1. Compute a Minimum Spanning Tree (MST) of G.
    2. Find the set :math:`O` of vertices with odd degree in the MST.
    3. Compute a Minimum Weight Perfect Matching (MWPM) on :math:`O`.
    4. Combine MST and matching into a multigraph (all degrees become even).
    5. Find an Eulerian circuit in the multigraph.
    6. Shortcut repeated vertices to obtain a Hamiltonian cycle.

    The resulting tour has weight at most :math:`\\frac{3}{2}` times the optimal.

2-Opt Heuristic
    Iteratively reverse segments of the tour to eliminate crossings, producing
    a locally optimal tour with no self-intersections.

References
    - Christofides, N. (1976). *Worst-case analysis of a new heuristic for
      the travelling salesman problem*. Carnegie Mellon University.
    - Karlin, A.R., Klein, N., Oveis Gharan, S. (2020). *A (Slightly) Improved
      Approximation Algorithm for Metric TSP*. STOC 2021.
"""

from typing import Any, List, Sequence, Tuple

import networkx as nx


def calculate_total_distance(path: Sequence[Any], G: nx.Graph) -> float:
    """Calculate the total length of a Hamiltonian path or cycle.

    :param path: Sequence of nodes representing the TSP tour (last node
        should equal the first for a closed cycle).
    :type path: Sequence[Any]

    :param G:  The complete graph with edge weights (``weight`` attribute
        on each edge).
    :type G: nx.Graph

    :return: Total distance of the path.
    :rtype: float

    Example:
        >>> import networkx as nx
        >>> G = nx.complete_graph(3)
        >>> G[0][1]['weight'] = 1.0
        >>> G[1][2]['weight'] = 2.0
        >>> G[0][2]['weight'] = 3.0
        >>> calculate_total_distance([0, 1, 2, 0], G)
        6.0
    """
    distance = 0.0
    for i in range(len(path) - 1):
        distance += G[path[i]][path[i + 1]]["weight"]
    return distance


def two_opt(path: List[Any], G: nx.Graph) -> List[Any]:
    """Refine a TSP tour using the 2-opt local search heuristic.

    The 2-opt heuristic iteratively replaces crossing edge pairs
    ``(i-1, i)`` and ``(j-1, j)`` with ``(i-1, j-1)`` and ``(i, j)``
    (by reversing the segment ``[i, j-1]``) whenever it reduces total
    distance.  This continues until a local optimum is reached.

    :param path: Initial TSP tour (list of nodes, last == first).
    :type path: List[Any]

    :param G: The complete graph with edge weights.
    :type G: nx.Graph

    :return: 2-opt refined tour (locally optimal).
    :rtype: List[Any]

    Example:
        >>> G = nx.complete_graph(4)
        >>> pts = [(0, 0), (1, 0), (1, 1), (0, 1)]
        >>> for u, v in G.edges():
        ...     G[u][v]['weight'] = ((pts[u][0]-pts[v][0])**2
        ...                        + (pts[u][1]-pts[v][1])**2)**0.5
        >>> tour = two_opt([0, 1, 2, 3, 0], G)
        >>> calculate_total_distance(tour, G) <= 5.0
        True
    """
    best_path = list(path)
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best_path) - 2):
            for j in range(i + 1, len(best_path)):
                if j - i == 1:
                    continue  # adjacent edges → no change

                # Reverse segment [i, j-1] to uncross
                new_path = (
                    best_path[:i] + best_path[i:j][::-1] + best_path[j:]
                )

                if calculate_total_distance(new_path, G) < calculate_total_distance(
                    best_path, G
                ):
                    best_path = new_path
                    improved = True
    return best_path


def christofides_tsp(G: nx.Graph) -> List[Any]:
    """Solve Metric TSP using the Christofides approximation algorithm.

    The algorithm produces a Hamiltonian cycle whose total weight is at most
    3/2 times the optimal.

    Steps:
        1. Minimum Spanning Tree (MST) of G.
        2. Identify odd-degree vertices in the MST.
        3. Minimum Weight Perfect Matching (MWPM) on odd-degree vertices.
        4. Combine MST + matching into an Eulerian multigraph.
        5. Find an Eulerian circuit.
        6. Shortcut repeated nodes to produce a Hamiltonian cycle.

    :param G: Complete graph with edge ``weight`` attributes satisfying the
        triangle inequality (Metric TSP).
    :type G: nx.Graph

    :return: Hamiltonian cycle as a list of nodes (last == first).
    :rtype: List[Any]

    Example:
        >>> G = nx.complete_graph(5)
        >>> for u, v in G.edges():
        ...     G[u][v]['weight'] = 1.0  # uniform → any tour works
        >>> tour = christofides_tsp(G)
        >>> len(tour) == 6  # 5 nodes + return to start
        True
        >>> calculate_total_distance(tour, G) > 0
        True
    """
    # 1. Minimum Spanning Tree
    mst = nx.minimum_spanning_tree(G, weight="weight")

    # 2. Odd-degree nodes in the MST
    odd_degree_nodes = [v for v, d in mst.degree() if d % 2 != 0]

    # 3. Minimum Weight Perfect Matching on odd-degree subgraph
    odd_subgraph = G.subgraph(odd_degree_nodes)
    matching = nx.min_weight_matching(odd_subgraph, weight="weight")

    # 4. Combine MST and matching into a multigraph
    multigraph = nx.MultiGraph(mst)
    multigraph.add_edges_from((u, v, G[u][v]) for u, v in matching)

    # 5. Eulerian circuit
    eulerian_circuit = list(nx.eulerian_circuit(multigraph))

    # 6. Shortcut repeated vertices → Hamiltonian cycle
    return _shortcut_eulerian(eulerian_circuit)


def _shortcut_eulerian(eulerian_circuit: List[Tuple[Any, Any]]) -> List[Any]:
    """Convert an Eulerian circuit to a Hamiltonian cycle by skipping repeats.

    :param eulerian_circuit: List of directed edges ``(u, v)`` forming an
        Eulerian circuit.
    :type eulerian_circuit: List[Tuple[Any, Any]]

    :return: Hamiltonian cycle as a list ``[v0, v1, ..., vn, v0]``.
    :rtype: List[Any]
    """
    path: List[Any] = []
    visited: set = set()
    for u, _v in eulerian_circuit:
        if u not in visited:
            path.append(u)
            visited.add(u)
    path.append(path[0])  # close the loop
    return path


def solve_christofides_2opt_tsp(G: nx.Graph) -> List[Any]:
    """Solve Metric TSP using Christofides + 2-Opt refinement.

    This is the recommended entry point.  It first computes a
    3/2-approximate tour via :func:`christofides_tsp`, then refines it
    with :func:`two_opt` local search to typically reduce the tour length
    further (often close to optimal for moderate :math:`n`).

    :param G: Complete graph with edge ``weight`` attributes satisfying the
        triangle inequality.
    :type G: nx.Graph

    :return: Refined Hamiltonian cycle (last node == first).
    :rtype: List[Any]

    Example:
        >>> G = nx.complete_graph(6)
        >>> for u, v in G.edges():
        ...     G[u][v]['weight'] = 1.0  # uniform weights
        >>> tour = solve_christofides_2opt_tsp(G)
        >>> len(tour) == 7
        True
        >>> nodes_visited = tour[:-1]
        >>> sorted(nodes_visited) == list(range(6))
        True
    """
    # Phase 1: Christofides initial tour
    initial_path = christofides_tsp(G)

    # Phase 2: 2-Opt refinement
    refined_path = two_opt(initial_path, G)

    return refined_path
