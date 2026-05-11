"""
Hadlock's Algorithm for Planar MAX-CUT
========================================

Hadlock's algorithm solves the **Maximum Cut** problem on planar graphs in
polynomial time by transforming it into a minimum weight perfect matching
problem on the planar dual graph.

The algorithm works as follows:

1. Find a planar embedding of the input graph.
2. Construct the dual graph where each face becomes a vertex.
3. Identify *odd faces* — faces whose boundary has an odd number of edges.
4. Build a complete graph on the odd-face vertices with edge weights equal
   to shortest-path distances in the dual graph.
5. Find a minimum weight perfect matching (MWPM) on this complete graph.
6. The primal edges that correspond to dual edges on the shortest paths
   between matched faces are the *excluded* edges.
7. The remaining primal edges form the maximum cut.

Reference
---------
Hadlock, F. O. (1975). "Finding a Maximum Cut of a Planar Graph in
Polynomial Time." *SIAM Journal on Computing*, 4(3), 221-225.
"""

from typing import Any, Dict, List, Set, Tuple

import networkx as nx


def _find_faces(
    embedding: nx.PlanarEmbedding,
) -> List[List[Any]]:
    """Extract all faces from a planar embedding.

    Each face is returned as a list of node IDs in cyclic order. The
    *outer* face is included as one of the returned faces.

    Parameters
    ----------
    embedding : nx.PlanarEmbedding
        A valid planar embedding of a graph.

    Returns
    -------
    list of list
        Each element is a list of nodes forming a face boundary.
    """
    visited: Set[Tuple[Any, Any]] = set()
    faces: List[List[Any]] = []
    for v in embedding.nodes():
        for w in embedding.neighbors(v):
            if (v, w) in visited:
                continue
            mark: Set[Tuple[Any, Any]] = set()
            face_nodes = list(
                embedding.traverse_face(v, w, mark_half_edges=mark)
            )
            visited.update(mark)
            faces.append(face_nodes)
    return faces


def _build_dual(
    G: nx.Graph,
    faces: List[List[Any]],
    weight: str,
) -> nx.Graph:
    """Build the dual graph from primal faces.

    Each face becomes a vertex in the dual.  Two dual vertices are
    connected if the corresponding faces share a primal edge.  The dual
    edge stores:

    - ``weight`` — the weight of the primal edge (or 1 if missing)
    - ``primal`` — the ``(u, v)`` tuple of the shared primal edge

    If two faces share multiple primal edges, only the connection with
    the *minimum* weight is kept (this is sufficient for shortest-path
    computations).

    Parameters
    ----------
    G : nx.Graph
        The primal graph (must contain the edge attributes).
    faces : list of list
        List of faces, each being a list of node IDs.
    weight : str
        Edge attribute name for weights.

    Returns
    -------
    nx.Graph
        The dual graph.
    """
    # ---- build edge → face mapping ----
    edge_faces: Dict[Tuple[Any, Any], List[int]] = {}
    for i, face in enumerate(faces):
        for j in range(len(face)):
            u, v = sorted((face[j], face[(j + 1) % len(face)]))
            key = (u, v)
            edge_faces.setdefault(key, []).append(i)

    # ---- build dual (handle parallel edges by keeping min weight) ----
    dual_G = nx.Graph()
    # (face_i, face_j) sorted → (min_weight, primal_edge)
    info: Dict[Tuple[int, int], Tuple[float, Tuple[Any, Any]]] = {}
    for e, face_ids in edge_faces.items():
        if len(face_ids) < 2:
            continue  # bridge / boundary edge
        w = G[e[0]][e[1]].get(weight, 1)
        for a in range(len(face_ids)):
            for b in range(a + 1, len(face_ids)):
                fi, fj = (
                    (face_ids[a], face_ids[b])
                    if face_ids[a] < face_ids[b]
                    else (face_ids[b], face_ids[a])
                )
                key = (fi, fj)
                if key not in info or w < info[key][0]:
                    info[key] = (w, e)

    for (fi, fj), (w, e) in info.items():
        dual_G.add_edge(fi, fj, weight=w, primal=e)

    return dual_G


def solve_hadlock_max_cut(
    G: nx.Graph, weight: str = "weight"
) -> Set[Tuple[Any, Any]]:
    r"""Solve MAX-CUT for a planar graph using Hadlock's algorithm.

    Parameters
    ----------
    G : nx.Graph
        A planar graph.  Edge weights should be stored under the
        attribute given by *weight* (default: ``'weight'``).  If an edge
        lacks this attribute, weight 1 is assumed.
    weight : str
        Edge attribute name for weights.

    Returns
    -------
    set of tuple
        A set of ``(u, v)`` edges (sorted tuples) that form the maximum
        cut.  The edges are guaranteed to form a bipartite subgraph.

    Raises
    ------
    nx.NetworkXException
        If *G* is not planar.

    Examples
    --------
    >>> import networkx as nx
    >>> from netlistx.hadlock import solve_hadlock_max_cut, validate_max_cut

    Build a simple triangle with weights:

    >>> G = nx.Graph()
    >>> G.add_edge(0, 1, weight=5)
    >>> G.add_edge(1, 2, weight=10)
    >>> G.add_edge(2, 0, weight=3)
    >>> cut = solve_hadlock_max_cut(G)
    >>> is_ok, val = validate_max_cut(G, cut)
    >>> is_ok
    True
    >>> val  # should be total - min_weight = 18 - 3 = 15
    15
    """
    # ---- 1. verify planarity & get embedding ----
    is_planar, embedding = nx.check_planarity(G)
    if not is_planar:
        raise nx.NetworkXException("Graph is not planar")

    # ---- 2. find faces ----
    faces = _find_faces(embedding)
    if not faces:
        # no faces → empty graph
        return set()

    # ---- 3. build dual graph ----
    dual_G = _build_dual(G, faces, weight)

    # ---- 4. identify odd faces ----
    odd_faces = [i for i, face in enumerate(faces) if len(face) % 2 == 1]

    if len(odd_faces) < 2:
        # Already bipartite — every edge can be in the cut
        return {tuple(sorted(e)) for e in G.edges()}

    if len(odd_faces) % 2 != 0:
        # The handshaking lemma for planar graphs guarantees an even
        # number of odd faces, but we guard against numerical / edge
        # cases by dropping the last odd face.
        odd_faces = odd_faces[:-1]
        if len(odd_faces) < 2:
            return {tuple(sorted(e)) for e in G.edges()}

    # ---- 5. all-pairs shortest paths in the dual ----
    dist = dict(nx.all_pairs_dijkstra_path_length(dual_G, weight="weight"))
    paths = dict(nx.all_pairs_dijkstra_path(dual_G, weight="weight"))

    # ---- 6. complete graph of odd faces with shortest-path weights ----
    complete_odd = nx.Graph()
    complete_odd.add_nodes_from(odd_faces)
    for i in range(len(odd_faces)):
        for j in range(i + 1, len(odd_faces)):
            u, v = odd_faces[i], odd_faces[j]
            if v in dist[u]:
                complete_odd.add_edge(u, v, weight=dist[u][v])

    # ---- 7. minimum weight perfect matching ----
    matching = nx.algorithms.matching.min_weight_matching(
        complete_odd, weight="weight"
    )

    # ---- 8. excluded primal edges from matching paths ----
    excluded: Set[Tuple[Any, Any]] = set()
    for u, v in matching:
        path = paths[u][v]
        for k in range(len(path) - 1):
            primal_edge = dual_G[path[k]][path[k + 1]].get("primal")
            if primal_edge is not None:
                excluded.add(tuple(sorted(primal_edge)))

    # ---- 9. max-cut = all primal edges \setminus excluded ----
    all_edges = {tuple(sorted(e)) for e in G.edges()}
    return all_edges - excluded


def validate_max_cut(
    G: nx.Graph,
    cut_edges: Set[Tuple[Any, Any]],
    weight: str = "weight",
) -> Tuple[bool, float]:
    """Validate that *cut_edges* forms a valid bipartite cut of *G*.

    A valid cut must induce a **bipartite subgraph** (i.e. no odd
    cycles).  The function also computes the total weight of the cut.

    Parameters
    ----------
    G : nx.Graph
        The original graph.
    cut_edges : set of tuple
        Edges in the proposed cut.
    weight : str
        Edge attribute name for weights (default: ``'weight'``).

    Returns
    -------
    (is_valid, cut_weight)
        is_valid : bool
            ``True`` if the cut subgraph is bipartite.
        cut_weight : float
            Sum of weights of all edges in the cut.
    """
    cut_graph = nx.Graph()
    cut_graph.add_nodes_from(G.nodes())
    cut_graph.add_edges_from(cut_edges)

    is_bipartite = nx.is_bipartite(cut_graph)

    cut_weight = sum(
        G[u][v].get(weight, 1) for u, v in cut_edges
    )

    return is_bipartite, cut_weight
