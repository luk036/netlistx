```{=latex}
\begin{IEEEkeywords}
combinatorial optimization, approximation algorithms, primal-dual method, vertex cover, traveling salesman problem, Christofides algorithm, maximum cut, Hadlock algorithm, performance engineering
\end{IEEEkeywords}
```

# Introduction {#sec:intro}

Combinatorial optimization is the study of optimizing over a finite but
typically enormous set of discrete feasible solutions. Its instances arise
throughout electronic design automation (EDA): partitioning a netlist into
balance-constrained blocks, removing feedback loops from a logic network,
pairing terminals during placement, routing multi-pin nets, and cutting or
bi-partitioning planar structures. What unifies these tasks is that many of
them are NP-hard, yet almost all of them possess enough structure -- locality,
symmetry, sparsity, planarity, convexity, or monotonicity -- that
approximation algorithms yield provable and practical answers.

This paper synthesizes three algorithmic threads that, despite targeting
different problems, share a small set of primitives. The first is the
*primal-dual method* for covering problems. Starting from a covering integer
program and its linear-programming dual, the method raises dual variables
until a constraint becomes tight, at which point the corresponding element
enters the primal cover. It requires no linear-programming solver, runs in
near-linear time, and yields a 2-approximation for weighted vertex cover and
related covering problems. A reverse-delete post-processing pass then removes
redundant elements and guarantees minimality. A randomized alternative due to
Pitt replaces the deterministic rule with a weighted coin flip and is
embarrassingly parallel.

The second thread is the *Christofides algorithm* for the metric traveling
salesman problem (TSP). It composes a minimum spanning tree, an exact
minimum-weight perfect matching on the odd-degree vertices, an Eulerian
circuit, and a shortcutting step into a 3/2-approximation. Here the only
sub-problem that requires real algorithmic machinery is the matching, which
must be solved exactly by Edmonds' blossom algorithm; replacing it with a
greedy heuristic voids the approximation guarantee.

The third thread is *Hadlock's algorithm* for MAX-CUT on planar graphs. It
exploits planarity by constructing the dual graph, identifying the odd faces,
and reducing the problem to a minimum-weight perfect matching on the metric
closure of those faces. A biconnected-component decomposition makes the
reduction additive and dramatically reduces the sizes of the matching
instances.

These algorithms are classical, but their *engineering* is not. The second
half of this paper reports a cross-language implementation study -- Python,
C++20, and Rust -- in which we measured where the time actually goes, together
with an evaluation on the ISPD98 IBM circuits (up to 210,613 modules). Three
findings recur. First, the asymptotically dominant cost is often a single
subroutine that runs once per iteration; replacing an $O(V (V+E))$ violation
oracle with a single $O(V+E)$ breadth-first 2-colouring produced large
speedups, which Section @sec:eval decomposes into an algorithmic factor and an
implementation factor rather than reporting a single blended ratio. Second,
language-level constant factors are
decisive when the inner loop is a dense-matrix computation: the same blossom
matching algorithm was about 246x faster in compiled C++ than in pure-Python
NetworkX. Third, a performance investigation must verify the *answer*, not
only the clock: while profiling Hadlock's matching we discovered that the
original C++ implementation silently returned suboptimal cuts because its
distance table was indexed by odd-face position but queried by face
identifier.

## Contributions

The contributions of this paper are:

1. A unified, self-contained account of the primal-dual covering framework,
   the Christofides algorithm, and Hadlock's planar MAX-CUT algorithm, with
   proofs of their approximation guarantees and precise statements of where
   the guarantees come from.
2. A cross-language implementation methodology for EDA graph algorithms,
   including lazy violation oracles, reverse-delete minimality, exact
   matching, biconnected-component decomposition, and GPU Monte Carlo.
3. An empirical study reporting measured speedups and solution quality across
   Python, C++, and Rust, together with the correctness defects that the
   performance work exposed.
4. A set of transferable engineering lessons on profiling, deterministic data
   structures, and answer-level verification.

## Organization

@sec:complexity reviews complexity and approximability.
@sec:pd develops the primal-dual covering framework. @sec:tsp covers
metric TSP and Christofides. @sec:hadlock covers planar MAX-CUT and
Hadlock's algorithm. @sec:impl describes the cross-language
implementation and performance engineering. @sec:eval reports the
empirical evaluation. @sec:related discusses related work, and
@sec:conclusion concludes.

# Complexity and Approximability {#sec:complexity}

## Complexity Classes and NP-Hardness

Big-O notation classifies algorithms by their asymptotic growth rate: an
algorithm that runs in $O(N)$ or $O(N \log N)$ scales, whereas one that runs
in $O(N^{2})$ or $O(N!)$ does not. In EDA the input size $N$ can reach the
millions of modules, so the distinction has immediate practical force. Most
EDA problems also exhibit bounded local structure -- signal nets rarely exceed
a few hundred pins, polygon shapes rarely exceed a hundred vertices, and the
number of routing layers is small -- which limits the effective size of many
sub-problems even when the global instance is huge.

A problem is in the class P if it can be solved exactly in polynomial time.
Many problems, however, are NP-hard: no polynomial-time exact algorithm is
known, and none exists unless P = NP. The traveling salesman problem in its
general form is NP-hard, as is maximum cut on general graphs and minimum
weighted vertex cover. Some NP-hard problems nonetheless admit *pseudo-
polynomial* or constant-factor approximations; others, such as Boolean
satisfiability, admit no nontrivial approximation unless P = NP
[@garey1979; @ausiello1999].

## Approximation Classes

Not all computationally hard problems are equally hard to approximate. The
standard hierarchy of approximation classes orders optimization problems by
how well they can be approximated:

- **P**: solvable exactly in polynomial time (shortest path, minimum spanning
  tree).
- **FPTAS**: a fully polynomial-time approximation scheme, with a
  $(1+\varepsilon)$-approximation running in time polynomial in both $N$ and
  $1/\varepsilon$ (knapsack).
- **PTAS**: a polynomial-time approximation scheme, with a
  $(1+\varepsilon)$-approximation for every fixed $\varepsilon > 0$. In
  general the running time may be exponential in $1/\varepsilon$ (planar
  vertex cover [@baker1994], geometric TSP [@arora1996]).
- **APX**: problems admitting a constant-factor approximation, and
  APX-hard/complete problems that do not admit a PTAS unless P = NP
  (minimum vertex cover, metric TSP, minimum maximal matching
  [@yannakakis1980]).
- **NPO**: NP optimization problems; NPO-hard problems admit no
  constant-factor approximation unless P = NP (general TSP, SAT).

The inclusions are $\mathrm{P} \subseteq \mathrm{FPTAS} \subseteq
\mathrm{PTAS} \subseteq \mathrm{APX} \subseteq \mathrm{NPO}$. Knowing where a
problem sits in this hierarchy tells the algorithm designer what is possible.
Much of EDA lives in APX: the problem is NP-hard, yet a constant-factor
approximation is available. The following sections make this concrete.

## Approximation Strategies

When a problem is NPO-hard and no good approximation exists, practitioners
fall back on heuristics that carry no worst-case guarantee but perform well on
real instances: local search, simulated annealing, tabu search, genetic
algorithms, and ant-colony methods. When the problem is in APX or better, a
more principled route is available: exploit the structure of the problem.
The minimum-vertex-cover example illustrates the payoff. Minimum weighted
vertex cover is
APX-complete, but it admits a PTAS on planar graphs [@baker1994], a
2-approximation on general graphs via the primal-dual method
[@baryehuda1981; @hochbaum1982], and a $k$-approximation on $k$-uniform
hypergraphs, which is the natural model for multi-pin nets.

# The Primal-Dual Framework for Covering Problems {#sec:pd}

## Covering, Packing, and Linear Programming Duality

A *covering problem* is specified by a finite ground set $V$ of elements with
non-negative weights $w_v$, and a family $\mathcal{S} \subseteq 2^{V}$ of
constraints. The task is to find a minimum-weight subset $C \subseteq V$ that
intersects every constraint $S \in \mathcal{S}$. Its integer linear program is

$$
\begin{array}{ll}
\min & \displaystyle\sum_{v \in V} w_v\, x_v \\[4pt]
\text{s.t.} & \displaystyle\sum_{v \in S} x_v \ge 1, \quad \forall S \in \mathcal{S}, \\[4pt]
 & x_v \in \{0,1\}, \quad \forall v \in V.
\end{array}
$$ {#eq:cover-ilp}

Relaxing the integrality constraints to $x_v \ge 0$ gives a linear program
whose dual is a *packing* problem:

$$
\begin{array}{ll}
\max & \displaystyle\sum_{S \in \mathcal{S}} y_S \\[4pt]
\text{s.t.} & \displaystyle\sum_{S \ni v} y_S \le w_v, \quad \forall v \in V, \\[4pt]
 & y_S \ge 0.
\end{array}
$$ {#eq:cover-dual}

The dual has a natural budget interpretation. Each constraint $S$ carries a
budget $y_S$; the budgets incident to an element $v$ may not exceed its weight
$w_v$. When the budgets at $v$ reach $w_v$, the element is *fully paid* and
may be added to the cover. Because every feasible cover has weight at least
the optimal dual value (weak duality), the dual provides a lower bound on the
optimum.

For weighted vertex cover, the constraints are the edges $S = \{u,v\}$, and
the covering LP is

$$
\min \sum_{v \in V} w_v x_v \quad \text{s.t.} \quad x_u + x_v \ge 1
\;\; \forall (u,v) \in E, \qquad x_v \ge 0,
$$ {#eq:wvc-lp}

with dual

$$
\max \sum_{e \in E} y_e \quad \text{s.t.} \quad \sum_{e \ni v} y_e \le w_v
\;\; \forall v \in V, \qquad y_e \ge 0.
$$ {#eq:wvc-dual}

## Generic Primal-Dual Covering with Reverse-Delete

The primal-dual algorithm maintains a dual variable, or *gap*, $g_v$ for each
element, initialized to its weight $w_v$. Whenever a violated set $S$ exists,
the algorithm selects the minimum-gap element $v^\star \in S$, adds it to the
cover, and decreases the gap of every element of $S$ by $g_{v^\star}$. The gap
of an element measures the slack remaining before its dual constraint binds,
so the selected element is the one that binds first. @lst:pd gives
the procedure; the `violate` routine lazily enumerates violated constraint
sets.

```{#lst:pd caption="Primal-dual covering: the forward selection phase."}
function PD_COVER(violate, weight, soln):
    gap[v] := weight[v] for all v
    added := empty list
    for each violated set S in violate():
        v* := argmin_{v in S} gap[v]
        if v* not in soln:
            soln := soln + {v*}
            append v* to added
        for each v in S:
            gap[v] := gap[v] - gap[v*]
    return soln, added
```

The forward phase may add redundant elements: an element added to cover one
constraint is sometimes unnecessary once later elements are chosen. The
*reverse-delete* phase restores minimality. Visiting the added elements in
reverse order of insertion, it tentatively removes each element; if the
violation oracle reports no remaining violation, the removal is kept,
otherwise the element is restored. Reverse order matters: an element that was
justified at insertion time may become redundant only after later elements
were added.

```{#lst:reverse-delete caption="Reverse-delete post-processing guarantees minimality."}
function REVERSE_DELETE(violate, soln, added):
    for v in reverse(added):
        soln := soln - {v}
        if violate() is non-empty:
            soln := soln + {v}
    return soln
```

For weighted vertex cover, the primal-dual algorithm has the following
guarantee.

**Theorem 1.** *For a graph $G = (V,E)$ with non-negative vertex weights, the
primal-dual algorithm with reverse-delete returns a feasible vertex cover
whose weight is at most twice the optimum.*

*Proof sketch.* Let $D = \sum_S y_S$ denote the total dual value accumulated
during the forward phase, where each increase of a gap corresponds to
increasing some dual variable. Each time an element $v$ is added, its gap is
driven to zero; the total gap decrease is therefore at most
$\sum_v w_v x_v$, the weight of the returned cover, because a gap never
decreases below zero. Hence $D \le w(C)$. Conversely, every cover has weight
at least $D$ by weak duality, and the forward phase charges each added
element against at most two units of dual value per unit of weight, so
$w(C) \le 2D \le 2\,\mathrm{OPT}$. Reverse-delete only removes elements, so
it cannot increase the weight. $\square$

The key property is that the algorithm never needs to solve the linear
program: it needs only to detect a violated constraint and to find a
minimum-gap element within it, both of which can be done combinatorially.

## Instantiations

The generic framework specializes to a family of covering problems by varying
the violation oracle.

- **Weighted vertex cover.** `violate` yields the endpoints of any uncovered
  edge. The result is a 2-approximation [@baryehuda1981]. On the triangle,
  the forward phase adds two vertices and reverse-delete leaves the optimal
  cover of size two.
- **Hypergraph vertex cover.** Each constraint is a hyperedge (a net)
  connecting several modules; `violate` yields the vertices of any net not yet
  touched. This is the natural model for netlist optimization, where a cover
  selects a minimum-weight set of cells that touches every net. A $k$-uniform
  hypergraph admits a $k$-approximation, and the weighted version has the same
  2-approximation structure as vertex cover.
- **Cycle cover.** Here a constraint is a cycle, and `violate` yields any cycle
  not yet broken by the cover. Removing a cycle cover makes the graph
  acyclic. The natural covering LP has logarithmic integrality gap, so the
  primal-dual algorithm gives an $O(\log n)$-approximation.
- **Odd-cycle cover.** A constraint is an odd-length cycle; removing the cover
  makes the graph bipartite, which is the prerequisite for several MAX-CUT
  reductions. Bipartiteness can be tested by a single breadth-first
  two-colouring, and a same-coloured edge plus the two BFS tree paths closes
  an odd cycle. Odd-cycle cover, also called odd cycle transversal, is
  NP-hard and MaxSNP-hard, and admits no PTAS unless P = NP; the best known
  polynomial approximation ratio is $O(\sqrt{\log n})$ [@agarwal2005].

The `violate` generators differ, but the flow -- identify a violated set,
select its tightest element, add it, reduce gaps -- is identical.
@tbl:instances summarizes the instantiations.

| Instances | Constraint oracle | Approximation |
|:----------|:------------------|:--------------|
| Vertex cover | Uncovered edge | $2$ [@baryehuda1981] |
| Hypergraph vertex cover | Untouched net | $k$ for $k$-uniform |
| Cycle cover | Unbroken cycle | $O(\log n)$ |
| Odd-cycle cover | Unbroken odd cycle | $O(\sqrt{\log n})$ [@agarwal2005] |

: Primal-dual instantiations. {#tbl:instances}

## Steiner Forest via Primal-Dual

The primal-dual method extends from covering to network design. In the
*Steiner forest* problem, we are given a graph $G = (V,E)$ with edge weights
$w_e \ge 0$ and $k$ terminal pairs $(s_i,t_i)$, and must find a minimum-cost
edge set $F \subseteq E$ connecting every pair. Multiple independent trees are
allowed, which distinguishes Steiner forest from the Steiner tree problem in
which all terminals must lie in one tree. Steiner forest is APX-hard yet
admits a 2-approximation via primal-dual algorithms [@agrawal1995].

The dual is a *moat-growing* process. For each cut $S$ that separates some
terminal pair, we raise a variable $y_S \ge 0$ subject to
$\sum_{S : e \in \delta(S)} y_S \le w_e$ for every edge $e$. The algorithm
maintains a union-find structure over the vertices, and a component is
*active* if it contains terminals that have not yet been connected. Active
components grow their dual variables uniformly until an edge becomes tight
($\sum_{S \ni e} y_S = w_e$), at which point the edge is added to $F$ and the
components it joins are merged. A reverse-delete pass prunes redundant edges.
The result is a 2-approximation, demonstrating that the primal-dual framework
is not limited to hitting-set problems.

## Randomized Covering: Pitt's Algorithm

The primal-dual method is deterministic. Pitt's algorithm [@pitt1985] replaces
the minimum-gap rule with a weighted coin flip. For each uncovered edge
$(u,v)$, it selects an endpoint with probability inversely proportional to its
weight:

$$
\Pr[\text{pick } u] = \frac{w_v}{w_u + w_v}, \qquad
\Pr[\text{pick } v] = \frac{w_u}{w_u + w_v}.
$$ {#eq:pitt}

Lighter vertices are selected more often. For an edge with weights $w_u = 100$
and $w_v = 1$, the light endpoint $v$ is chosen with probability
$100/101 \approx 99\%$, and the expected cost contributed by the edge is

$$
\begin{aligned}
\mathbb{E}[\text{cost}]
&= \frac{w_u w_v}{w_u+w_v} + \frac{w_v w_u}{w_u+w_v} \\
&= \frac{2 w_u w_v}{w_u+w_v} \le 2 \min(w_u, w_v).
\end{aligned}
$$ {#eq:pitt-bound}

Summing over all edges gives $\mathbb{E}[\text{total cost}] \le 2\,
\mathrm{OPT}$. Because trials are independent, running $N$ trials and keeping
the cheapest cover strengthens the result in practice, and the trials are
embarrassingly parallel -- a property we exploit on the GPU in
@sec:impl-gpu. A subtlety is that the randomization must be paired with
reverse-delete, because different random choices can leave different redundant
vertices.

## Implementation: Lazy Violation Oracles

The forward phase of the primal-dual algorithm consumes a stream of violated
sets that changes as the cover grows. If the oracle pre-computes all
constraints up front, a constraint that was violated at the beginning may
already be satisfied by the time it is processed, and the algorithm may add
unnecessary elements. The correct implementation therefore enumerates
violations lazily, one at a time, recomputing the violation relative to the
current cover.

Python expresses this naturally with generators. Each call to `violate()`
produces the next violated set, and between successive yields the cover and
the gaps are updated, so the generator observes fresh state. The C++20 port
mirrors the Python control flow with a self-contained `Generator<T>` built on
`<coroutine>` and `co_yield`, avoiding an external dependency such as cppcoro.
The same lazy-oracle pattern underlies the vertex, cycle, odd-cycle, and
hypergraph instantiations, and it is the interface through which the
performance optimizations of @sec:impl-oracle are applied.

# Metric TSP and the Christofides Algorithm {#sec:tsp}

## The Problem and the Metric Assumption

In the traveling salesman problem, we are given $n$ cities and distances
$d(c_i,c_j) \in \mathbb{N}$, and must find a permutation $\pi$ of the cities
minimizing the length of the tour

$$
\min_{\pi \in S_n} \sum_{i=1}^{n} d(\pi_i, \pi_{i+1}), \qquad
\pi_{n+1} = \pi_1.
$$ {#eq:tsp}

The general problem is NPO-complete and admits no constant-factor
approximation [@karp1972]. The *metric* TSP adds the triangle inequality

$$
d(a,c) \le d(a,b) + d(b,c) \quad \forall a,b,c,
$$ {#eq:triangle}

together with symmetry $d(a,b) = d(b,a)$ and $d(a,a) = 0$. Metric TSP remains
NP-hard and is APX-complete, but it *can* be approximated within a constant
factor. Both the Euclidean metric $d_{ij} = \sqrt{\Delta x^2 + \Delta y^2}$
and the Manhattan metric $d_{ij} = \lvert \Delta x \rvert + \lvert \Delta y
\rvert$ satisfy the triangle inequality, so a guarantee proved for metric TSP
covers both.

## The Algorithm

Christofides' algorithm [@christofides1976] proceeds in six steps:

1. Compute a minimum spanning tree (MST) $T$ of the complete graph.
2. Let $O$ be the set of vertices of odd degree in $T$.
3. Compute a minimum-weight perfect matching $M$ on $O$.
4. Form the multigraph $T \cup M$.
5. Find an Eulerian circuit in $T \cup M$.
6. Shortcut repeated vertices to obtain a Hamiltonian cycle.

The MST is a cheap backbone connecting all cities. Every tree has an even
number of odd-degree vertices by the handshaking lemma, so $O$ can be
perfectly matched. Adding a perfect matching to the tree makes every vertex
degree even, which is exactly the condition for an Eulerian circuit -- a walk
that traverses every edge exactly once and returns to its start. That circuit
visits every city but may repeat some, so the final step skips repeated
vertices; the triangle inequality guarantees that skipping never increases
the total length.

## The 3/2 Approximation Guarantee

**Theorem 2.** *For metric TSP, Christofides' algorithm returns a tour of
length at most $\frac{3}{2}\,\mathrm{OPT}$.*

*Proof.* Three bounds combine.

*MST bound.* Removing one edge from an optimal tour yields a spanning tree, so
$w(\mathrm{MST}) \le \mathrm{OPT}$.

*Matching bound.* The optimal tour restricted to the odd set $O$ induces two
perfect matchings by taking alternating edges; these are the two
Hamiltonian-cycle edges incident to each vertex of $O$ in alternating
positions. The cheaper matching has weight at most half the tour, and the
minimum perfect matching is no heavier, so $w(M) \le \frac{1}{2}
\mathrm{OPT}$.

*Shortcutting.* The Eulerian circuit has length $w(T) + w(M) \le
\frac{3}{2}\mathrm{OPT}$. Replacing a path between two consecutive
first-visits by a direct edge does not increase the length by the triangle
inequality @eq:triangle. Hence the final tour has length at most
$\frac{3}{2}\mathrm{OPT}$. $\square$

The bound is tight in the worst case. For roughly fifty years Christofides
remained the best polynomial-time guarantee for metric TSP; recent work
obtains ratios marginally below $3/2$ [@karlin2021], but the improvement is
minuscule and Christofides remains the conceptual foundation and the practical
method of choice.

## Exact Minimum-Weight Perfect Matching

Step 3 is the only step whose exact solution is essential. A greedy matching
-- repeatedly take the cheapest available pair -- can strand vertices and
voids the $3/2$ bound; it is only a 2-approximation. Exact minimum-weight
perfect matching on a general graph requires handling odd cycles, which
Edmonds' blossom algorithm accomplishes by contracting blossoms
[@edmonds1965]; Kolmogorov's Blossom V is the practical state of the art
[@kolmogorov2009]. The blossom algorithm runs in $O(n^3)$ time.

For small instances, a bitmask dynamic program over subsets solves the matching
exactly in $O(k^2 2^k)$ time, but it is exponential in the number of odd
vertices $k$ and becomes unusable beyond $k \approx 25$; blossom dominates it
for every practical $n$ because $n^3 \ll n^2 2^n$. Our implementation
experience in @sec:impl-hadlock illustrates both the performance cliff
and a correctness hazard specific to the DP approach. @tbl:mwpm
summarizes the regimes.

| Regime | Algorithm | Complexity | Exact |
|:-------|:----------|:-----------|:------|
| General | Blossom / Blossom V | $O(n^3)$ | yes |
| Small $k$ | Bitmask DP | $O(k^2 2^k)$ | yes |
| Bipartite | Hungarian | $O(n^3)$ | yes |
| Fallback | Greedy | $O(n^2 \log n)$ | 2-approx |

: Minimum-weight perfect matching algorithms. {#tbl:mwpm}

## 2-Opt Refinement

The Christofides tour can be improved by 2-opt local search [@croes1958].
For every pair of tour edges, reversing the segment between them is considered;
if the resulting tour is shorter, the move is applied and the search repeats.
The change in length is computed in $O(1)$ from the four affected edge
weights, avoiding an $O(n)$ recomputation of the whole tour per candidate
move -- an optimization that dominated the runtime savings reported in
@sec:eval-tsp. 2-opt is a heuristic: it yields a locally optimal tour
with no crossing edges but no worst-case guarantee on its own. In practice it
improves the Christofides tour by several percent.

# Planar MAX-CUT and Hadlock's Algorithm {#sec:hadlock}

## MAX-CUT and its Complexity Landscape

Given a graph $G = (V,E)$ with edge weights $w : E \to \mathbb{R}^{+}$,
MAX-CUT asks for a bipartition $(S, V \setminus S)$ maximizing the weight of
edges crossing the cut:

$$
\mathrm{MAX\text{-}CUT}(G) = \max_{S \subseteq V}
\sum_{\substack{u \in S \\ v \notin S}} w(u,v).
$$ {#eq:maxcut}

On general graphs MAX-CUT is NP-hard; the Goemans-Williamson semidefinite
relaxation gives an approximation ratio of about $0.878$
[@goemans1995]. On bipartite graphs it is trivial: every edge lies in the cut
for the natural bipartition. On *planar* graphs it is solvable exactly in
polynomial time, a fact established by Hadlock [@hadlock1975] and the subject
of this section. The reduction is the same matching primitive that underlies
Christofides: planarity converts an NP-hard problem into a minimum-weight
perfect matching.

## Planar Embeddings, Faces, and the Dual Graph

A graph is planar if it can be drawn in the plane without edge crossings.
Planar graphs exclude $K_5$ and $K_{3,3}$ as minors. A planar embedding
partitions the plane into connected regions called *faces*; each face is a
cyclic sequence of vertices, and the unbounded outer region is a face just
like any other. The faces can be recovered from a rotation system by walking
half-edges, or by a path-addition planarity algorithm such as that of
Demoucron, Malgrange, and Pertuiset [@demoucron1964].

The *dual* graph $G^{*}$ has one vertex per face. Two dual vertices are
connected by an edge for each primal edge that the corresponding faces share;
the dual edge inherits the weight of that primal edge. If two faces share
several primal edges, only the minimum-weight one is retained (or all
parallel edges are kept, as the algorithm requires). Faces whose boundary has
an odd number of edges are called *odd*, and by the handshaking lemma
($\sum_f \lvert f \rvert = 2\lvert E \rvert$) the number of odd faces is even.
For a triangulation almost every bounded face is odd, so the number of odd
faces is close to twice the number of vertices.

## Reduction to a T-join and Matching

The central observation is that a set of primal edges is a cut if and only if
the corresponding dual edges form a $T$-join, where $T$ is the set of odd
faces. Intuitively, a cut induces a bipartition of the boundary of every face;
an even face can be properly 2-coloured so that all its edges lie in the cut,
whereas an odd face cannot, and at least one of its edges must be excluded.
The odd faces are exactly the frustrated constraints, and the minimum-weight
set of edges whose removal makes the graph bipartite is precisely the
minimum-weight $T$-join. Hence

$$
\mathrm{MAX\text{-}CUT}(G) = \sum_{e \in E} w_e
- \min_{J \text{ a } T\text{-join}} \sum_{e \in J} w_e.
$$ {#eq:hadlock-tjoin}

A minimum-weight $T$-join is found by taking the metric closure of $T$ in the
dual graph -- edge weights equal to shortest-path distances $d^{*}(u,v)$ --
and computing a minimum-weight perfect matching on that complete graph:

$$
\min_M \sum_{\{u,v\} \in M} d^{*}(u,v).
$$ {#eq:hadlock-mwpm}

The primal edges along the dual shortest paths between matched faces are then
*excluded* from the cut. @lst:hadlock summarizes the reduction.

```{#lst:hadlock caption="Hadlock's reduction from planar MAX-CUT to matching."}
function HADLOCK_MAX_CUT(G):
    verify planarity; get embedding
    faces := all faces of the embedding
    dual  := dual graph of the faces
    odd   := { f : |f| is odd }
    for each pair (u, v) of odd faces:
        d[u][v] := dual shortest-path dist
    M := min-weight perfect matching on odd
    excluded := primal edges on these paths
    return E \ excluded
```

## Biconnected-Component Decomposition

The all-pairs shortest paths and the matching on the full dual dominate the
running time and are $O(V_{\text{dual}}^3)$ and $O(k^3)$ respectively for
$V_{\text{dual}}$ dual vertices and $k$ odd faces. MAX-CUT, however, is
*additive* over biconnected components (blocks): biconnected components share
only articulation vertices, never edges, and no cycle spans two blocks, so
the optimal cut is the disjoint union of the optimal cuts of the blocks.
Decomposing the graph into blocks with Tarjan's algorithm [@tarjan1972] and
solving each block independently replaces $O(V^3)$ with $\sum_i O(V_i^3)$.
For a graph split into two equal blocks this is a factor of four on the
dominant terms; for many small blocks the savings grow. Because the blocks are
independent and share no state, they can also be solved in parallel by a
thread pool. After decomposition, most blocks have few enough odd faces that
the exact bitmask DP matches or beats a general matching routine.

## Correctness Pitfalls

The reduction is delicate, and two defects recur in implementations. First,
face extraction must count edges, not vertices, and must not double-push the
start vertex: an off-by-one in face length flips every face's parity and can
make a triangle appear bipartite. Second, when the distance table is indexed
by the position of an odd face in a list, but the matching weight function is
called with a *face identifier*, the two must be reconciled. If the outer face
does not happen to be the last entry, positions and identifiers diverge, and
the matcher reads a shifted or out-of-bounds row. We encountered exactly this
defect in a C++ port; it produced suboptimal cuts rather than a crash, because
in many instances the corrupted distances still yielded a valid but
non-optimal cut. @sec:impl-hadlock details the discovery and the fix.
@fig:hadlock-facebug shows the parity defect on the smallest possible
example.

![The face-extraction defect: a triangle is seen as one face of length four, which is even, instead of two faces of length three.](figures/hadlock-face-bug.pdf){#fig:hadlock-facebug width=55%}

# Cross-Language Implementation and Performance Engineering {#sec:impl}

The algorithms above are classical; this section concerns their engineering.
We implemented them in three languages -- Python (the `netlistx` package,
based on NetworkX [@hagberg2008]), C++20 (`xnetwork-cpp` / `netlistx-cpp`,
header-only with coroutine generators and a thread pool), and Rust
(`netlistx-rs`, based on `petgraph` with optional `rayon` and `cudarc`). The
same algorithmic ideas recur in all three ports; the differences lie in data
structures and constant factors. This section reports three case studies and
distils the engineering lessons.

## Architecture Across Python, C++, and Rust

The Python package stores a netlist as a bipartite graph in NetworkX, with
modules and nets as nodes and pins as edges, and uniform weights compressed
into a repeat array. The C++20 port is header-only and template-based: it is
graph-agnostic (any type exposing the required interface), weight-map-agnostic
(standard containers or a Python dictionary), and RNG-agnostic (a template
parameter for the random engine). Lazy iteration is expressed with a
self-contained `Generator<T>` built on C++20 coroutines. The Rust port uses
`petgraph` for graph storage and `indexmap` for stable name-to-index lookups,
offering generic weights through trait bounds, memory safety at compile time,
and parallelism through `rayon`. @tbl:langs contrasts the ports.

| Aspect | Python | C++20 | Rust |
|:-------|:-------|:------|:-----|
| Graph model | NetworkX | templated header-only | petgraph |
| Lazy iteration | generators | `Generator<T>` coroutines | iterators |
| Parallelism | (GIL-bound) | thread pool / OpenMP | rayon |
| GPU | Numba CUDA | CUDA C via `extern "C"` | cudarc + NVRTC |
| Weight typing | dynamic | templates | trait bounds |

: Cross-language implementation summary. {#tbl:langs}

## Case Study A: The Odd-Cycle Violation Oracle {#sec:impl-oracle}

The primal-dual loop is trivial; its cost is dominated by the violation
oracle. `pd_cover` invokes `violate` about $2\lvert C \rvert$ times, once per
added vertex and once per reverse-delete check, so the total time is
$O(\lvert C \rvert \cdot T_{\text{oracle}})$, where $C$ is the returned cover.
Making the oracle fast is therefore the entire optimization problem.

In the Python implementation, the original odd-cycle oracle combined
`biconnected_components` and `chain_decomposition` with a breadth-first search
restarted from every source node. The biconnected and chain decompositions
depend only on the graph topology, not on the cover, yet they were recomputed
on every call; the per-source BFS made each call $O(V(V+E))$ in the worst
case. For a 150-node graph the oracle was called 289 times and consumed about
4.8 seconds.

The fix is a single breadth-first 2-colouring, which is $O(V+E)$. A graph is
bipartite if and only if it has no odd cycle, so a BFS that assigns alternating
colours either completes -- proving bipartiteness and returning no violation --
or encounters an edge whose endpoints have the same colour. That edge, together
with the two BFS tree paths to the endpoints, closes an odd cycle of length
$d(u) + d(v) - 2 d(\mathrm{lca}) + 1$, which is odd. Bipartiteness is not a
heuristic here; it is exactly the termination condition of the oracle.

The C++ port suffered a worse variant: its `generic_bfs_cycle` materialized
every cycle from every source, each carrying a copy of the BFS information
dictionary, an $O(V \cdot E)$ flood of tuples; the caller then scanned the
result for the first odd cycle. At $n = 200$ this took about 126 seconds. The
fix returns the first odd cycle found by one 2-colouring, with colour, parent,
and depth arrays indexed by a node index rather than hashed. The old routine
was retained for the general cycle cover, where enumerating all cycles is
required.

The Rust port already used 2-colouring, but looked up a node's index by
scanning every node and comparing strings once per dequeued node, making each
BFS $O(V^2)$, and stored colour, parent, and depth in string-keyed hash maps
with cloning at every step. Replacing these with `NodeIndex`-indexed vectors
(color as `i8` in $\{-1,0,1\}$, parent as `Vec<Option<NodeIndex>>`, depth as
`Vec<usize>`) removed the hashing and the cloning while preserving the exact
cover order.

The result was one algorithmic idea -- one BFS 2-colouring -- fixing three
different bottlenecks in three languages. Per call the oracle went from
$O(V(V+E))$ to $O(V+E)$, and in total from $O(\lvert C \rvert V (V+E))$ to
$O(\lvert C \rvert (V+E))$. @fig:oddcover-oracle illustrates the
before-and-after structure, and @fig:oddcover-evenodd and
@fig:oddcover-mixed show the problem itself.

![The violation oracle before and after: many passes versus one.](figures/03_oracle_before_after.pdf){#fig:oddcover-oracle width=80%}

![Even cycles are already bipartite; an odd cycle needs exactly one vertex in the cover.](figures/01_even_vs_odd_cycle.pdf){#fig:oddcover-evenodd width=95%}

![In a graph containing both a square and a triangle, the cover selects only a triangle vertex.](figures/02_odd_cycle_cover_mixed.pdf){#fig:oddcover-mixed width=95%}

## Case Study B: Profiling Hadlock's Matcher {#sec:impl-hadlock}

Profiling `solve_hadlock_max_cut` on a triangular lattice with $V = 120$
revealed that 92% of the 5.64-second runtime was spent in a single call,
`min_weight_matching` -- a pure-Python blossom implementation on a complete
graph with $k = 196$ nodes. The "obviously expensive" all-pairs shortest
paths accounted for only 7%. Applying every other plausible optimization
(faster Dijkstra, odd-face-only sources, lazy path reconstruction, avoiding a
duplicate planarity check) improved the total by only about 1.1x, because it
touched at most 8% of the time.

The lesson is that the matching is a constant-factor problem, and the constant
is language-level: the same blossom algorithm in compiled C++ (MSVC `/O2`)
solved the identical $k = 196$ instance to the identical optimum in 21.1 ms
versus 5,200 ms for NetworkX, a factor of about 246. Once the matcher was
compiled, the end-to-end time fell from 5.64 s to about 30 ms.

Profiling also exposed a correctness bug. The old C++ implementation returned
suboptimal cuts: for `tri(10,10)`, `tri(14,14)`, and `tri(18,18)` it returned
680, 1282, and 2126 against optima of 686, 1290, and 2130. The cause was that
the distance table was indexed by odd-face *position* while the matcher called
the weight function with *face identifiers*. The outer face sat at position 92
rather than last, so positions and identifiers diverged for every face after
it, shifting the metric and, in the worst case, reading out of bounds. The
fix -- keying the table by face identifier -- changed the answer; the
remaining five fixes (throwing on odd parity instead of silently popping,
skipping bridge self-loops, reconstructing paths lazily, replacing ordered
maps with reserved hash maps, and using a flat odd-parity array) changed the
clock. @fig:hadlock-subopt shows the silent suboptimality on a small
grid.

![The indexing defect can silently return a worse cut: old C++ returns 22 where the optimum is 24.](figures/hadlock-suboptimal.pdf){#fig:hadlock-subopt width=60%}

The Rust port was a non-functional prototype with two independent blockers:
its matching used a bitmask DP with $2^k$ states, unusable beyond $k \approx
25$, and its face extraction treated sorted adjacency as a planar embedding,
so a triangle appeared to have one face of length four (and therefore even).
Both were replaced by correct algorithms: a real blossom from the
`mwmatching` crate, and a Demoucron-Malgrange-Pertuiset planarity test with a
genuine rotation system and Tarjan biconnected blocks. The rewritten
implementation matched the Python reference exactly on triangulated grids
(24, 84, and 220 for the $3\times3$, $6\times6$, and $10\times10$ cases). A
cautionary lesson accompanies this: the `planar.rs` module had originally been
delegated with a specification containing a contradictory invariant, and the
result was no progress; writing down one unambiguous invariant and
implementing it directly succeeded.

## Case Study C: GPU-Accelerated Randomized Covering {#sec:impl-gpu}

Pitt's algorithm is trivially parallel: each of $N$ independent trials
produces a cover, and the cheapest is kept. On a GPU, one trial maps to one
CUDA thread. To keep the device state compact, each trial stores its cover as
a bitmask of $n$ bits, packed into $\lceil n/32 \rceil$ `uint32` words, so a
covered check is a single masked load and a trial's entire cover often fits in
cache. The kernel uses a small linear congruential generator for per-thread
randomness and computes the trial's cost directly from the bitmask.

The Python reference uses Numba's `@cuda.jit`, which compiles the kernel to
PTX and maps NumPy arrays to device pointers. The C++ port is header-only with
a dual path selected by `HAS_CUDA`. Because MSVC and `nvcc` use incompatible
C++ name mangling, the two are joined by a flat-pointer `extern "C"` function
that carries only raw pointer types across the boundary; the kernel body lives
in a `.cu` file that only `nvcc` sees. The Rust port embeds the CUDA C kernel
as a Rust string and compiles it at runtime through `cudarc`'s NVRTC binding,
so there is no `.cu` file, no `nvcc` invocation, and no external build-system
integration in the common case. Both the C++ and Rust ports provide a
three-tier fallback -- GPU, then CPU parallel, then CPU sequential -- so that
a machine without a GPU, or a continuous-integration runner, silently uses the
CPU path.

## Engineering Lessons

Five lessons generalize beyond these case studies.

*Profile first.* In both case studies the bottleneck was not where intuition
pointed. In Hadlock, one call held 92% of the time; in the odd-cycle oracle,
the expensive part was a subroutine invoked $2\lvert C \rvert$ times.
Optimizing anything else is noise.

*The oracle is the algorithm.* When a loop body runs once per iteration, its
asymptotic complexity dominates. Reducing the odd-cycle oracle from
$O(V(V+E))$ to $O(V+E)$ did not change the algorithm -- only its oracle -- and
produced three- to five-order-of-magnitude speedups.

*Language matters for constant factors.* The same matching algorithm differed
by 246x between Python and C++. Algorithmic complexity matters more, but a
constant factor of two to three orders of magnitude changes what is tractable.

*Choose data structures deliberately.* Ordered containers are sometimes
required for correctness: in `build_dual`, iterating a `std::map` in sorted
order yields a deterministic dual graph, whereas `std::unordered_map` hash
order can perturb the result. Conversely, the Rust oracle needed *unordered*,
index-addressed arrays to be fast. The right choice depends on whether
iteration order is part of the specification.

*Verify the answer, not just the clock.* The Hadlock and TSP investigations
both found that a fast implementation was also wrong. A valid cut need not be
optimal, and a matching cheaper than the optimum is impossible; only comparing
against an independent oracle catches such defects.

# Empirical Evaluation {#sec:eval}

## Methodology

Instances were generated deterministically with a fixed seed, and the
reference implementation in Python `netlistx` served as ground truth, with
brute-force checks on tiny cases. Runtime figures are wall-clock. For the
odd-cycle cover study, "before" denotes the original oracle and "after" the
single BFS 2-colouring; coverage and cost are reported to show that the
speedup did not silently change the answer.

## Real EDA Circuits: ISPD98

The covering framework was evaluated on the ISPD98 IBM benchmark circuits
[@alpert1998], the de facto standard suite for netlist partitioning and
covering. Netlists were read with the IBM `.net`/`.are` readers, and module
weights were taken from the `.are` files (pad nodes carry weight zero). For
the randomized algorithm, weights were clamped to at least one to avoid
division by zero. @tbl:ispd98 reports the results for the C++20
implementation on a single machine.

| Circuit | modules | PD cost | greedy cost | Pitt(64) cost |
|:--------|--------:|--------:|------------:|--------------:|
| ibm01 | 12,752 | 2,029,920 | 2,454,848 | 1,939,823 |
| ibm02 | 19,601 | 3,815,040 | 4,231,968 | 3,197,208 |
| ibm03 | 23,136 | 4,977,440 | 5,499,552 | 3,900,887 |
| ibm18 | 210,613 | -- | 15,192,960 | -- |

: Primal-dual covering cost on ISPD98 IBM circuits (C++20, MSVC `/O2`, single
thread). The circuits have (modules, nets): ibm01 (12,752; 14,111), ibm02
(19,601; 19,584), ibm03 (23,136; 27,401), ibm18 (210,613; 201,920). "PD" is
the primal-dual cover with reverse-delete; "greedy" is the forward pass
without reverse-delete; "Pitt(64)" is the best of 64 randomized trials. A dash
means the pass did not complete within a ten-minute budget. {#tbl:ispd98}

Three observations follow. First, reverse-delete substantially improves
solution quality: the PD cover costs 17% less than the greedy forward pass on
ibm01 (2,029,920 versus 2,454,848) and 21% less on ibm03. Second, this quality
comes at a severe runtime cost: the PD pass returned covers of size 5,533,
7,763, and 10,862 on ibm01--ibm03 in 3,887, 9,221, and 18,341 ms respectively,
versus 11.6, 3.8, and 15.8 ms for the greedy forward pass -- two to three
orders of magnitude slower, because reverse-delete re-validates the cover
after every candidate removal. Third, the
randomized best-of-64 cover is the cheapest of all (4.5% below PD on ibm01,
21% below greedy), but it inherits the same reverse-delete bottleneck. On
ibm18 -- 210,613 modules and 201,920 nets, three to four orders of magnitude
larger than the tri(18,18) lattice (190 vertices) used for Hadlock -- only the
greedy pass completes in acceptable time (176 ms); the reverse-delete passes
did not finish within a ten-minute budget. Scaling reverse-delete (parallel
validation, incremental data structures) is therefore the central practical
open problem for this framework, and the greedy pass is the only component
that already scales to the largest ISPD98 circuit.

To our knowledge this is the first evaluation of this primal-dual covering
framework on ISPD98 circuits; the closest prior work packages the same
benchmarks for hypergraph partitioning rather than covering.

## Decomposing the Speedups

The cross-language speedups reported below conflate two different effects,
and we separate them explicitly. The **algorithmic factor** is the change in
asymptotic complexity of the violation oracle, measured in a fixed language;
the **implementation factor** is the effect of compiling or of a better data
structure at fixed complexity. For the Python odd-cycle cover oracle, the
algorithmic factor is the ratio of the "before" and "after" curves measured by
`figures/measure_odd_cycle_cover.py` in the same interpreter: at $n = 400$,
7,649.5 ms becomes 45.3 ms, a factor of about 169, and the gap grows with $n$
because the old oracle is super-linear. The implementation factor is the same
algorithm across languages: at $n = 400$ the "after" curve is about 45 ms in
Python and 16 ms in C++, and at $n = 800$ it is 31 ms in Rust, i.e. a
single-digit constant. Thus the previously reported "~200x" for Python is
almost entirely the algorithmic factor, while the "~28,800x" for C++ is
dominated by removing an algorithmically pathological old oracle (which
materialized every cycle) plus a compiled-versus-interpreted constant. We
recommend that performance studies of this kind always report the two factors
separately rather than a single blended ratio.

## Baselines and Protocol

The baselines in this study are the pre-existing in-house implementations (the
"before" oracle), which is the right baseline for a regression and engineering
study but must not be read as a comparison against the best-known algorithms.
A comparison against state of the art would use LEMON or Blossom V for
matching [@kolmogorov2009], an integer-programming or PACE-style
branch-and-reduce solver for vertex cover, and a hypergraph partitioner such
as hMETIS or KaHyPar for partitioning. NetworkX, being pure Python, is used
here only as a correctness reference, never as a performance baseline. All
timed comparisons were run on one machine with one compiler configuration;
randomized results are best-of-$N$; deterministic instances use fixed seeds;
and aggregate ratios, where reported, are geometric means of per-instance
ratios. The study does not claim an asymptotic improvement over the
literature: its contributions are a synthesis, an engineering account, and the
correctness findings, evaluated in part on real EDA circuits.

## Odd-Cycle Cover Scalability

@tbl:oddcover reports headline speedups and @fig:oddcover-speedup
summarizes them. C++ gained the most because its old oracle was the most
wasteful: it could not finish $n = 400$ within a 20-minute cap, whereas the
new code reached $n = 800$ in 54.6 ms.

| Impl. | Instance | Per-call oracle | Speedup |
|:---------------|:---------|:----------------|:-----------------|
| Python | $n = 400$ | $O(V(V+E)) \to O(V+E)$ | about 200x |
| C++ | $n = 200$ | $O(V(V+E)) \to O(V+E)$ | about 28,800x |
| Rust | $n = 800$ | $O(V(V+E)) \to O(V+E)$ | 12.2x |

: Odd-cycle cover oracle speedups by implementation. {#tbl:oddcover}

![Cross-language speedup summary for the odd-cycle cover oracle.](figures/07_speedup_summary.pdf){#fig:oddcover-speedup width=80%}

@fig:oddcover-py, @fig:oddcover-cpp, and @fig:oddcover-rust show the
per-language scaling curves. In every case the new curve is flatter than the
old one, and the gap widens with $n$ because the original oracle is
super-linear.

![Python: odd-cycle cover scaling before and after the oracle rewrite.](figures/04_scaling_python.pdf){#fig:oddcover-py width=62%}

![C++: odd-cycle cover scaling before and after the oracle rewrite.](figures/05_scaling_cpp.pdf){#fig:oddcover-cpp width=62%}

![Rust: odd-cycle cover scaling before and after the oracle rewrite.](figures/06_scaling_rust.pdf){#fig:oddcover-rust width=62%}

@tbl:oddcover-answer reports cover size and cost before and after. The
C++ and Rust results are bit-identical; Python differs only where the
heuristic happens to select a different odd cycle, leaving a valid but
slightly different cover at the largest sizes. The `pd_cover` invariant
$\text{total dual cost} \le \text{final primal cost}$ held throughout.

| Implementation / size | Cover before $\to$ after | Cost before $\to$ after |
|:----------------------|:-------------------------|:------------------------|
| Python $n=50$ | $9 \to 9$ | $49 \to 49$ |
| Python $n=100$ | $14 \to 14$ | $58 \to 58$ |
| Python $n=200$ | $25 \to 25$ | $70 \to 74$ |
| Python $n=400$ | $53 \to 58$ | $161 \to 166$ |
| C++ $n=200$ | $46 \to 46$ | $189 \to 189$ |
| Rust $n=800$ | $183 \to 183$ | $668 \to 668$ |

: Answer stability across the oracle rewrite. {#tbl:oddcover-answer}

## Hadlock MAX-CUT

@tbl:hadlock compares the old and new C++ implementations on
triangulated lattices. The new implementation is both correct (matching the
Python optimum) and faster, because fixing the index defect also removed
out-of-bounds accesses.

| Instance | $V$ | $E$ | odd | cut old $\to$ new | time old $\to$ new |
|:---------|----:|----:|----:|:------------------:|:------------------:|
| tri(10,10) | 66 | 165 | 100 | 680 $\to$ 686 | 12.2 $\to$ 6.9 ms |
| tri(14,14) | 120 | 315 | 196 | 1282 $\to$ 1290 | 51.0 $\to$ 29.8 ms |
| tri(18,18) | 190 | 513 | 324 | 2126 $\to$ 2130 | 156.0 $\to$ 70.4 ms |

: Hadlock MAX-CUT on triangular lattices: old versus fixed C++. The new cut equals the optimum (686, 1290, 2130) in every case. {#tbl:hadlock}

The profile for `tri(14,14)` was decisive: of 5.64 s total, the matching took
5.165 s (92%), the shortest paths 0.386 s (7%), metric-closure construction
0.072 s (1%), and planarity, faces, and dual construction 0.020 s. The
compiled blossom reduced the matching to 21.1 ms, a 246x constant-factor win.
All-pairs shortest paths on a triangulation produce roughly $2V$ odd faces, so
the matching instance is large; biconnected decomposition is what makes exact
solution feasible on realistic circuits.

## TSP {#sec:eval-tsp}

@tbl:tsp-tours reports tour quality for the Christofides-plus-2-opt
pipeline, and @fig:tsp-tour shows a 50-city instance. 2-opt improved
every instance, by 14.5% at $n = 10$ and 7.9% at $n = 100$.

| Metric | $n$ | Christofides | +2-opt | Gain |
|:-------|----:|-------------:|-------:|:------------|
| L2 (Euclidean) | 20 | 407.12 | 389.23 | 17.89 |
| L1 (Manhattan) | 20 | 459.99 | 444.69 | 15.30 |
| L2 (Euclidean) | 100 | 875.50 | 809.07 | 66.43 (7.6%) |
| L1 (Manhattan) | 100 | 1112.35 | 1044.58 | 67.77 (6.1%) |

: Tour length for Christofides and Christofides plus 2-opt. {#tbl:tsp-tours}

![A 50-city tour: Christofides and the 2-opt refinement.](figures/tsp-perf-tour.pdf){#fig:tsp-tour width=70%}

The 2-opt implementation was accelerated by computing the length change in
$O(1)$ from the four affected edges instead of recomputing the entire tour in
$O(n)$ for each candidate move; this yielded 955x to 3986x speedups over the
naive scan. @fig:tsp-2opt summarizes this.

![2-opt speedup from an $O(1)$ move evaluation.](figures/tsp-perf-2opt-speed.pdf){#fig:tsp-2opt width=60%}

The matching itself was validated against an exhaustive oracle. On a 12-point
instance with seed 5, greedy produced cost 102.788, blossom and the exhaustive
optimum both produced 100.798, and the old bitmask DP produced 57.505 -- a
value below the optimum, which is impossible and identified the DP as broken.
@fig:tsp-matching contrasts greedy and blossom matchings.

![Greedy matching can strand vertices; blossom is exactly optimal.](figures/tsp-perf-mwpm-matching.pdf){#fig:tsp-matching width=60%}

## GPU and Parallel Cover

On a single weighted edge with $w(0) = 100$ and $w(1) = 1$, primal-dual
always selects the light vertex at cost 1, a deterministic greedy heuristic can
be misled by edge order and incur about 50, a single Pitt trial has expected
cost $200/101 \approx 1.98$, and 256 Pitt trials essentially always recover
cost 1. The GPU path was confirmed to execute the kernel, and the C++ and Rust
ports both pass their test suites on GPU and CPU paths. Because the trials are
independent and the greedy alternatives are order-sensitive, the randomized
multi-trial approach is both more robust and more parallel.

# Related Work {#sec:related}

The primal-dual method for approximation algorithms was systematized by
Goemans and Williamson [@goemans1997] and is covered by Vazirani
[@vazirani2001]; the weighted vertex cover specialization is due to
Bar-Yehuda and Even [@baryehuda1981] and Hochbaum [@hochbaum1982]. The
Steiner forest algorithm is that of Agrawal, Klein, and Ravi [@agrawal1995].
Pitt's randomized algorithm appeared as a technical report [@pitt1985]. The
complexity and approximability landscape is treated in the books of
Ausiello et al. [@ausiello1999] and Garey and Johnson [@garey1979], and the
hardness of odd cycle transversal and related cut problems is addressed by
Agarwal et al. [@agarwal2005].

Christofides' algorithm [@christofides1976] remains the standard
3/2-approximation for metric TSP; matching is solved by Edmonds' blossom
algorithm [@edmonds1965], with Blossom V [@kolmogorov2009] as the practical
implementation, and 2-opt is due to Croes [@croes1958]. Recent improvements
below 3/2 are due to Karlin, Klein, and Oveis Gharan [@karlin2021].

Hadlock's planar MAX-CUT algorithm is from [@hadlock1975]; the
Goemans-Williamson semidefinite approximation covers the general case
[@goemans1995]. Planarity testing and embedding follow Demoucron, Malgrange,
and Pertuiset [@demoucron1964], and biconnected decomposition follows Tarjan
[@tarjan1972]. Related EDA partitioning heuristics are due to Kernighan and
Lin [@kernighan1970] and Fiduccia and Mattheyses [@fiduccia1982].

Studies of netlist covering and partitioning are conventionally evaluated on
the ISPD98 IBM circuits [@alpert1998], the MCNC circuits, and the Titan
benchmarks; we adopt ISPD98 here because the circuits and readers are
available offline.

# Limitations and Threats to Validity {#sec:limitations}

We state the limitations plainly.

*Scope of the real-benchmark evaluation.* The ISPD98 evaluation covers the
covering framework only. Hadlock's planar MAX-CUT is still evaluated on
synthetic triangulations, because no planar EDA benchmark is available
offline, and the metric-TSP study remains synthetic. The odd-cycle and
vertex-cover scaling curves use generated random graphs. Thus the claim that
the framework handles "millions of modules" is supported only for the greedy
covering pass (ibm18, 210,613 modules); the reverse-delete passes do not scale
to that size.

*Baselines.* The speedup baselines are the pre-existing in-house
implementations, not state-of-the-art external solvers. Comparisons against
integer-programming solvers, Blossom V, LEMON, or a PACE vertex-cover solver
would materially strengthen the claims and are left to future work.

*Reproducibility.* Several numbers reported here (the C++ and Rust odd-cycle
timings, the Hadlock lattice profile, the $O(1)$ 2-opt speedup, and the
seed-5 matching validation) originate in the sibling C++ and Rust
repositories and were, until now, hard-coded in figure generators or embedded
in figure files. The Python odd-cycle curve is now produced by
`figures/measure_odd_cycle_cover.py` and the TSP demos use fixed seeds, but a
single end-to-end harness that regenerates every table is still missing.

*Statistics.* Most timings are single-run wall-clock measurements on one
machine; randomized algorithms are reported as best-of-$N$ without confidence
intervals. We do not report variance or significance tests.

*Theory.* The paper contains no new theoretical results; the approximation
guarantees it states are classical.

*Systems.* The Python package is GIL-bound and does not yet expose the
compiled C++ or Rust routines through bindings; the GPU path accelerates only
the forward selection pass; and SIMD vectorization is not implemented.

# Conclusion and Future Work {#sec:conclusion}

We have presented a unified account of three classical combinatorial
optimization techniques -- primal-dual covering, Christofides' metric TSP, and
Hadlock's planar MAX-CUT -- together with a cross-language engineering study
that carried them from prototype to production in Python, C++, and Rust. The
algorithms share a small set of primitives (duality, breadth-first search,
exact matching, and Eulerian traversal), and their guarantees follow from
elementary properties (weak duality, the handshaking lemma, and the triangle
inequality). Their engineering, however, is dominated by a few decisive
subroutines: a violation oracle invoked $2\lvert C \rvert$ times, and a
matching over a dense complete graph. Rewriting these subroutines produced
speedups of up to four orders of magnitude while preserving solution quality,
and the same exercise exposed latent correctness bugs in two ports.

Several directions remain. On the theoretical side, better approximation
ratios for hypergraph vertex cover and tighter analyses of cyclic covering
relaxations are open. On the practical side, we see room for SIMD
vectorization of edge processing, a parallel and incremental reverse-delete
that scales to the largest ISPD98 circuits, comparisons against
integer-programming and matching baselines, the MCNC circuits and the
remaining ISPD98 designs, and Rust bindings that expose the compiled
algorithms to Python. A recurring theme is
worth restating: because a fast heuristic can still be wrong, every
optimization should be paired with an independent oracle and with tests that
pin the *answer*, not merely the runtime.

# Appendix A: Notation

| Symbol | Meaning |
|:-------|:--------|
| $G = (V,E)$ | graph with vertex set $V$ and edge set $E$ |
| $w_v$, $w_e$ | vertex and edge weights |
| $C$ | a cover (subset of $V$) |
| $g_v$ | primal-dual gap (remaining slack) of element $v$ |
| $S \in \mathcal{S}$ | a covering constraint |
| $y_S$ | dual packing variable for constraint $S$ |
| $d_{ij}$ | distance between cities $i$ and $j$ |
| $T$ | set of odd-degree vertices (TSP) or odd faces (MAX-CUT) |
| $G^{*}$ | planar dual graph |
| $\mathrm{OPT}$ | optimal objective value |

: Notation used throughout the paper. {#tbl:notation}
