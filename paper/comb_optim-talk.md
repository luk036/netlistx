# Outline

### Outline

```{=latex}
{\scriptsize\tableofcontents[hideallsubsections]\vspace{-2.5pt}}
```

# The Landscape

## Approximation in EDA

### Why EDA needs approximation algorithms

- Almost every EDA task is a **combinatorial optimization problem**: partitioning a netlist under balance constraints, removing feedback loops, pairing terminals during placement, routing multi-pin nets, cutting or bi-partitioning planar structures
- Most are **NP-hard** . . . yet almost all possess exploitable structure: locality, symmetry, sparsity, planarity, convexity, monotonicity [@garey1979; @ausiello1999]
- Input size reaches **millions of modules** &mdash; an $O(N^2)$ routine does not scale, so asymptotic design is a practical necessity
- EDA also has **bounded local structure** (nets rarely exceed a few hundred pins; few routing layers), which keeps sub-problems tractable even when the global instance is huge

### The approximation hierarchy

- $\mathrm{P} \subseteq \mathrm{FPTAS} \subseteq \mathrm{PTAS} \subseteq \mathrm{APX} \subseteq \mathrm{NPO}$ tells the designer what is achievable
    - P: shortest path, MST
    - FPTAS: knapsack &mdash; polynomial in $N$ and $1/\varepsilon$
    - PTAS: planar vertex cover [@baker1994], geometric TSP [@arora1996]
    - APX: vertex cover, metric TSP &mdash; constant-factor ratios exist
    - NPO-hard: general TSP, SAT &mdash; no constant ratio unless P $=$ NP
- Most of EDA lives in **APX**: NP-hard, yet a constant-factor approximation is available
- When a problem is NPO-hard, only **heuristics** remain: local search, simulated annealing, tabu search, genetic and ant-colony methods

### Three threads, one toolbox 🧩

- **Primal-dual covering** &mdash; 2-approx for vertex cover, hypergraph cover, cycle and odd-cycle cover, and Steiner forest
- **Christofides metric TSP** &mdash; the classic $3/2$-approximation
- **Hadlock planar MAX-CUT** &mdash; NP-hard in general, exact in polynomial time on planar graphs

All three share a few primitives: **LP duality**, **breadth-first search**, **exact matching**, **Eulerian traversal**. Their guarantees follow from three elementary facts: *weak duality*, the *handshaking lemma*, and the *triangle inequality*.

# Primal-Dual Covering

## The method

### Covering as an LP, and its dual as budgets

A covering problem: pick a minimum-weight set $C \subseteq V$ that hits every constraint $S \in \mathcal{S}$:

$$\min \sum_{v \in V} w_v x_v \quad \text{s.t.} \quad \sum_{v \in S} x_v \ge 1 \;\; \forall S \in \mathcal{S}, \;\; x_v \in \{0,1\}$$

The LP dual is a *packing* problem with a budget reading: each constraint $S$ carries a budget $y_S$, and the budgets incident to $v$ may not exceed its weight $w_v$:

$$\max \sum_{S \in \mathcal{S}} y_S \quad \text{s.t.} \quad \sum_{S \ni v} y_S \le w_v, \;\; y_S \ge 0$$

When the budgets at $v$ reach $w_v$, the element is **fully paid** and may enter the cover. By **weak duality**, every feasible cover costs at least the optimal dual value.

### The generic algorithm: forward pass + reverse-delete

```python
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

- The gap $g_v$ measures the **slack** before element $v$ binds, so the minimum-gap element is the one that binds first &mdash; the forward phase never solves the LP
- The forward pass can add **redundant** elements; **reverse-delete** restores minimality: visit `added` in reverse, drop each element unless a violation reappears
- Reverse order matters: an element justified at insertion may become redundant only *after* later elements were added

### Theorem 1: a 2-approximation

**Theorem (Bar-Yehuda &amp; Even 1981; Hochbaum 1982).** For non-negative vertex weights, primal-dual with reverse-delete returns a feasible cover with weight $w(C) \le 2\,\mathrm{OPT}$ [@baryehuda1981; @hochbaum1982].

*Proof sketch.* Let $D = \sum_S y_S$ be the dual accumulated.
1. Each added element is driven to zero gap, and a gap never goes negative \Rightarrow $D \le w(C)$.
2. By weak duality every cover costs at least $D$, and each unit of cover weight is charged against at most **two** units of dual \Rightarrow $w(C) \le 2D \le 2\,\mathrm{OPT}$.
3. Reverse-delete only removes elements, so it cannot increase the weight. $\square$

The key property: **no LP solver is needed** &mdash; only the violation oracle and a minimum-gap element.

## Instantiations and engineering

### One framework, many instantiations

```{=latex}
\begin{center}
\footnotesize
\begin{tabular}{lll}
\hline
Instances        & Constraint oracle   & Approximation \\
\hline
Vertex cover     & Uncovered edge      & $2$ \\
Hypergraph vertex cover & Untouched net & $k$ ($k$-uniform) \\
Cycle cover      & Unbroken cycle      & $O(\log n)$ \\
Odd-cycle cover  & Unbroken odd cycle  & $O(\sqrt{\log n})$ \\
\hline
\end{tabular}
\end{center}
```

The last row matters for EDA: removing an odd-cycle cover makes the netlist **bipartite**, the prerequisite for several MAX-CUT reductions [@agarwal2005]. Beyond hitting sets, the same method solves **Steiner forest** by *moat growing* with a union-find &mdash; again a 2-approximation [@agrawal1995].

### Pitt's algorithm: randomized, and embarrassingly parallel

Replace "pick the tightest" with a weighted coin flip:

$$\Pr[\text{pick } u] = \frac{w_v}{w_u + w_v}, \qquad \mathbb{E}[\text{cost}] = \frac{2 w_u w_v}{w_u + w_v} \le 2 \min(w_u, w_v)$$

Summing over edges: $\mathbb{E}[\text{total cost}] \le 2\,\mathrm{OPT}$ [@pitt1985]. Trials are independent, so run $N$ of them and keep the cheapest. Example: an edge with $w_u = 100, w_v = 1$ &mdash; the light endpoint is chosen with probability $100/101 \approx 99\%$, while an order-sensitive greedy can be misled to cost $\approx 50$. The randomization must still be paired with reverse-delete, because different choices leave different redundant vertices.

### Lazy violation oracles

- The oracle is called about **$2|C|$ times** (once per added vertex, once per reverse-delete check) \Rightarrow its cost dominates the whole run
- Precomputing all constraints up front is *wrong*: a set violated early may already be satisfied by the time it is processed
- Correct pattern: enumerate violations **lazily**, one at a time, relative to the current cover
    - Python: `generator` yielding the next violated set
    - C++20: a self-contained `Generator<T>` built on coroutines (`co_yield`), no external dependency
    - Rust: `Iterator`s
- This interface is where the engineering story begins . . .

# Christofides Metric TSP

## The algorithm

### The problem, and why the metric matters

$$\min_{\pi \in S_n} \sum_{i=1}^{n} d(\pi_i, \pi_{i+1}) \qquad \text{with } \pi_{n+1} = \pi_1$$

- **General TSP** is NPO-complete: no constant-factor approximation exists unless P $=$ NP [@karp1972]
- **Metric TSP** adds symmetry and the **triangle inequality** $d(a,c) \le d(a,b) + d(b,c)$ \Rightarrow in APX, a constant ratio is possible
- Both Euclidean $d_{ij} = \sqrt{\Delta x^2 + \Delta y^2}$ and Manhattan $d_{ij} = |\Delta x| + |\Delta y|$ distances are metric, so guarantees transfer to placement-style costs

### Christofides in six steps

```{=latex}
\begin{center}
\begin{tikzpicture}[x=3.4cm,y=1.8cm]
  \node[nblue,text width=3.0cm]   (mst) at (0,1)   {1. MST $T$};
  \node[nyellow,text width=3.0cm] (odd) at (1,1)   {2. Odd-degree set $O$};
  \node[ngreen,text width=3.0cm]  (mat) at (2,1)   {3. Min-weight matching $M$};
  \node[ngreen,text width=3.0cm]  (uni) at (2,0)   {4. $T \cup M$};
  \node[nblue,text width=3.0cm]   (eul) at (1,0)   {5. Eulerian circuit};
  \node[nyellow,text width=3.0cm] (tour) at (0,0)  {6. Shortcut $\Rightarrow$ tour};
  \draw[ar] (mst) -- (odd);
  \draw[ar] (odd) -- (mat);
  \draw[ar] (mat.south) -- (uni.north);
  \draw[ar] (uni) -- (eul);
  \draw[ar] (eul) -- (tour);
\end{tikzpicture}
\end{center}
```

Every tree has an even number of odd-degree vertices (handshaking lemma), so $O$ can be perfectly matched; adding $M$ makes all degrees even &mdash; exactly the Eulerian condition. The final shortcut never lengthens the tour by the triangle inequality.

### Theorem 2: the $3/2$ guarantee

**Theorem (Christofides 1976).** For metric TSP, Christofides' algorithm returns a tour of length at most $\tfrac{3}{2}\,\mathrm{OPT}$ [@christofides1976].

*Proof.* Three bounds combine:
1. **MST bound:** removing one edge of an optimal tour leaves a tree \Rightarrow $w(\mathrm{MST}) \le \mathrm{OPT}$.
2. **Matching bound:** the optimal tour restricted to $O$ splits into two perfect matchings; the cheaper one has weight $\le \tfrac{1}{2}\,\mathrm{OPT}$, so $w(M) \le \tfrac{1}{2}\,\mathrm{OPT}$.
3. **Shortcutting:** replacing a path between consecutive first visits by a direct edge never increases length (triangle inequality).

\Rightarrow tour length $\le w(T) + w(M) \le \tfrac{3}{2}\,\mathrm{OPT}$. The bound is tight; even decades of later work only barely beats it [@karlin2021].

## Making it exact and fast

### Matching is the only exact step

```{=latex}
\begin{center}
\footnotesize
\begin{tabular}{llll}
\hline
Regime     & Algorithm             & Complexity      & Exact \\
\hline
General    & Blossom / Blossom V   & $O(n^3)$        & yes \\
Small $k$  & Bitmask DP            & $O(k^2 2^k)$    & yes \\
Bipartite  & Hungarian             & $O(n^3)$        & yes \\
Fallback   & Greedy                & $O(n^2 \log n)$ & 2-approx \\
\hline
\end{tabular}
\end{center}
```

Greedy matching **strands vertices** and is only a 2-approximation &mdash; replacing blossom with greedy voids the $3/2$ guarantee [@edmonds1965; @kolmogorov2009]. The bitmask DP is exact but exponential in the odd set $k$: unusable beyond $k \approx 25$.

![Greedy can strand vertices; blossom is exactly optimal.](figures/tsp-perf-mwpm-matching.pdf){width=42%}

### Polishing with 2-opt, and measured tour quality

- 2-opt tests every pair of tour edges and reverses the segment if it shortens the tour [@croes1958]
- The move gain is evaluated in **$O(1)$** from the four affected edges, not by an $O(n)$ tour recomputation &mdash; a **955x &ndash; 3986x** speedup over the naive scan
- Measured gain: 14.5% at $n = 10$; **7.6% (L2) / 6.1% (L1)** at $n = 100$

```{=latex}
\begin{center}
\footnotesize
\begin{tabular}{llrrr}
\hline
Metric & $n$ & Christofides & +2-opt & Gain \\
\hline
L2 (Euclidean) & 20  & 407.12   & 389.23   & 17.89 \\
L1 (Manhattan) & 20  & 459.99   & 444.69   & 15.30 \\
L2 (Euclidean) & 100 & 875.50   & 809.07   & 66.43 (7.6\%) \\
L1 (Manhattan) & 100 & 1112.35  & 1044.58  & 67.77 (6.1\%) \\
\hline
\end{tabular}
\end{center}
```

# Planar MAX-CUT: Hadlock

## The reduction

### MAX-CUT: the complexity cliff

$$\mathrm{MAX\text{-}CUT}(G) = \max_{S \subseteq V} \sum_{\substack{u \in S \\ v \notin S}} w(u,v)$$

- **General graphs:** NP-hard; Goemans-Williamson SDP gives $\approx 0.878$ [@goemans1995]
- **Bipartite graphs:** trivial &mdash; every edge crosses the natural bipartition
- **Planar graphs:** **exact polynomial time** [@hadlock1975] &mdash; planarity converts an NP-hard problem into a minimum-weight perfect matching, the same primitive Christofides needs

### Cut $\Leftrightarrow$ T-join on the dual

```{=latex}
\begin{center}
\begin{tikzpicture}[x=2.7cm,y=1.2cm]
  \node[nblue]   (g)    at (0,1)   {Planar $G$};
  \node[nyellow] (dual) at (1,1)   {Dual $G^{*}$};
  \node[nred]    (odd)  at (2,1)   {Odd faces $T$};
  \node[ngreen]  (mm)   at (2,0)   {MWPM on metric closure};
  \node[nblue]   (cut)  at (0,0)   {Cut $= E \setminus J$};
  \draw[ar] (g) -- (dual);
  \draw[ar] (dual) -- (odd);
  \draw[ar] (odd.south) -- node[right,font=\scriptsize]{metric closure $d^*(u,v)$} (mm.north);
  \draw[ar] (mm) -- (cut);
\end{tikzpicture}
\end{center}
```

Odd faces are the **frustrated constraints** of 2-colouring; the minimum-weight set of edges whose removal makes the graph bipartite is a **minimum $T$-join**:

$$\mathrm{MAX\text{-}CUT}(G) = \sum_{e \in E} w_e \; - \min_{J \text{ a } T\text{-join}} \sum_{e \in J} w_e$$

A minimum $T$-join is a **minimum-weight perfect matching** on the odd faces with shortest-path distances $d^*(u,v)$ in the dual.

### Biconnected-component decomposition

- MAX-CUT is **additive** over biconnected components: blocks share only articulation vertices, and no cycle spans two blocks
- Replaces $O(V^3)$ all-pairs / matching with $\sum_i O(V_i^3)$ &mdash; two equal blocks already gain **factor 4** on the dominant terms
- Blocks share no state \Rightarrow they can be solved in parallel by a thread pool
- After decomposition, most blocks have few odd faces, where the **exact bitmask DP** matches or beats a general blossom [@tarjan1972]

## Implementation matters

### Hadlock MAX-CUT: old versus fixed

```{=latex}
\begin{center}
\footnotesize
\begin{tabular}{lrrrll}
\hline
Instance & $V$ & $E$ & odd & cut old $\to$ new & time old $\to$ new \\
\hline
tri(10,10) & 66  & 165 & 100 & 680 $\to$ 686   & 12.2 $\to$ 6.9 ms \\
tri(14,14) & 120 & 315 & 196 & 1282 $\to$ 1290 & 51.0 $\to$ 29.8 ms \\
tri(18,18) & 190 & 513 & 324 & 2126 $\to$ 2130 & 156.0 $\to$ 70.4 ms \\
\hline
\end{tabular}
\end{center}
```

The new cut reaches the optimum (**686, 1290, 2130**) in every case; fixing the index defect also removed out-of-bounds accesses. For `tri(14,14)`: of 5.64 s total, the matching took **5.165 s (92%)**, shortest paths 7%, metric closure 1%.

### Two traps that compile cleanly 🐛

::: {.columns}
::: {.column width="47%"}
**Face length parity.** Face extraction must count *edges*, not vertices, and must not double-push the start vertex. A triangle seen as one face of length four is even &mdash; it looks bipartite!

![The face-extraction defect on the smallest example.](figures/hadlock-face-bug.pdf){width=62%}
:::
::: {.column width="47%"}
**Position vs. identifier indexing.** The distance table was indexed by odd-face *position* but queried by *face identifier*. When the outer face sat at position 92 rather than last, the matcher read shifted rows &mdash; and returned a **silent suboptimal cut** (22 vs. optimum 24 below).

![Silent suboptimality on a small grid.](figures/hadlock-suboptimal.pdf){width=62%}
:::
:::

Both defects were found only because we verified the **answer**, not the runtime.

# Engineering Across Python, C++, Rust

## One algorithm, three ports

### Three ports, one algorithm

```{=latex}
\begin{center}
\footnotesize
\begin{tabular}{llll}
\hline
Aspect         & Python              & C++20                    & Rust \\
\hline
Graph model    & NetworkX            & templated header-only    & petgraph \\
Lazy iteration & generators          & Generator<T> coroutines & iterators \\
Parallelism    & (GIL-bound)         & thread pool / OpenMP     & rayon \\
GPU            & Numba CUDA          & CUDA C via extern "C"    & cudarc + NVRTC \\
Weight typing  & dynamic             & templates                & trait bounds \\
\hline
\end{tabular}
\end{center}
```

The algorithm is identical; the differences are data structures and constant factors [@hagberg2008]. We now report three case studies and distil the lessons.

## Case studies

### Case A: the odd-cycle violation oracle ⚡

::: {.columns}
::: {.column width="50%"}
The oracle is called $\approx 2\lvert C \rvert$ times, so the total time is $O(\lvert C \rvert \cdot T_{\mathrm{oracle}})$.

**Before:** recomputed `biconnected_components` + `chain_decomposition` on every call, BFS from every source &mdash; $O(V(V+E))$ per call (150 nodes, 289 calls, $\approx 4.8$ s).

**After:** one **BFS 2-colouring** &mdash; $O(V+E)$. A same-coloured edge plus the two tree paths closes an odd cycle of length $d(u)+d(v)-2d(\mathrm{lca})+1$.

One idea fixed three bottlenecks: Python's restart-from-every-source BFS, C++'s materialization of *every* cycle ($n{=}200 \approx 126$ s), Rust's string-keyed hashmaps.
:::
::: {.column width="50%"}
![Many passes versus one.](figures/03_oracle_before_after.pdf){width=100%}
:::
:::

### Case B: profile the matcher

- `tri(14,14)`: 5.64 s total &mdash; **92%** in one call, `min_weight_matching` (pure-Python blossom), 5.165 s; shortest paths only 7%
- Optimizing the "obviously expensive" 7% bought $\approx 1.1\times$; the bottleneck was a **constant factor**, not the asymptotics
- The *same* blossom in compiled C++ (MSVC `/O2`): **21.1 ms vs. 5,200 ms** &mdash; a **246x** language-level constant; end-to-end 5.64 s &rarr; $\approx 30$ ms
- Profiling also surfaced the real defect: old C++ reported suboptimal cuts (680/1282/2126 vs. optima 686/1290/2130)
- Fixing the *answer* (indexing) and fixing the *clock* (data structures) are different changes

### Case C: Pitt's algorithm on the GPU

- One randomized trial = one CUDA thread; each cover is an $n$-bit **bitmask** in $\lceil n/32 \rceil$ `uint32` words &mdash; a covered-test is one masked load; per-thread LCG for randomness
- Three implementations of one kernel:
    - Python: Numba `@cuda.jit` &rarr; PTX, NumPy arrays as device pointers
    - C++: flat-pointer `extern "C"` bridge &mdash; MSVC and `nvcc` cannot share C++ mangling; kernel lives in a `.cu` file
    - Rust: kernel embedded as a string, compiled at runtime via **NVRTC** &mdash; no `.cu`, no `nvcc`, no build-system hook
- **Three-tier fallback** GPU &rarr; CPU parallel &rarr; CPU sequential, so a CI machine silently uses the CPU path

### Five engineering lessons

1. **Profile first.** In both case studies the bottleneck was not where intuition pointed (92% in one matching call; a subroutine invoked $2\lvert C \rvert$ times).
2. **The oracle is the algorithm.** $O(V(V+E)) \to O(V+E)$ without changing the algorithm &rarr; three to five orders of magnitude.
3. **Language sets constant factors.** The identical blossom algorithm differed by **246x** between Python and C++.
4. **Choose data structures deliberately.** `std::map` (sorted) gives a *deterministic* dual graph where `unordered_map` hash order perturbs results &mdash; while the Rust oracle needed *index-addressed* arrays to be fast.
5. **Verify the answer, not just the clock.** A valid cut need not be optimal, and a matching cheaper than the optimum is impossible &mdash; only an independent oracle catches that.

# Evaluation and Conclusions

## ISPD98

### ISPD98: real EDA circuits at last

```{=latex}
\begin{center}
\footnotesize
\begin{tabular}{lrrrr}
\hline
Circuit & modules & PD cost & greedy cost & Pitt(64) cost \\
\hline
ibm01 & 12,752  & 2,029,920 & 2,454,848 & 1,939,823 \\
ibm02 & 19,601  & 3,815,040 & 4,231,968 & 3,197,208 \\
ibm03 & 23,136  & 4,977,440 & 5,499,552 & 3,900,887 \\
ibm18 & 210,613 & ---       & 15,192,960 & --- \\
\hline
\end{tabular}
\end{center}
```

C++20, MSVC `/O2`, single thread; dash: no result within a ten-minute budget [@alpert1998]. Circuits in (modules, nets): ibm01 (12,752; 14,111), ibm02 (19,601; 19,584), ibm03 (23,136; 27,401), ibm18 (210,613; 201,920).

### Observations and the rest of the story

::: {.columns}
::: {.column width="52%"}
1. **Quality:** reverse-delete beats the forward greedy pass by **17% on ibm01** and **21% on ibm03**.
2. **Cost:** reverse-delete re-validation makes PD **two to three orders** of magnitude slower (3,887 vs. 11.6 ms on ibm01).
3. **Randomization:** Pitt(64) is the cheapest of all (4.5% below PD, 21% below greedy) but inherits the same reverse-delete bottleneck.
4. **Scaling:** on ibm18 (210,613 modules) only greedy completes (176 ms); reverse-delete does not finish in ten minutes &mdash; *the central open problem*.
:::
::: {.column width="48%"}
5. **Hadlock:** fixing the indexing defect reached the optimum everywhere (680 &rarr; **686**, 1282 &rarr; **1290**, 2126 &rarr; **2130**) and ran about **2x faster**.
6. **Matching validation** (12 points, seed 5): greedy 102.788; blossom and the exhaustive oracle both 100.798; the old bitmask DP returned **57.505 below the optimum** &mdash; impossible.
7. **GPU Pitt:** one edge with $w(0){=}100,\ w(1){=}1$ &mdash; PD cost 1, order-sensitive greedy $\approx 50$, and **256 trials always recover cost 1**.
:::
:::

## Decomposing the speedup

### Algorithmic vs. implementation factors

- **Algorithmic factor** (same language): Python $n{=}400$: 7,649.5 ms &rarr; 45.3 ms &asymp; **169x**, and the gap grows with $n$ because the old oracle is super-linear
- **Implementation factor** (same complexity): Python 45 ms vs. C++ 16 ms at $n{=}400$, Rust 31 ms at $n{=}800$ &mdash; **single-digit constants**
- So "~200x" (Python) is almost entirely algorithmic, while "~28,800x" (C++) is dominated by an algorithmically *pathological* old oracle plus a compiled constant
- Reporting one blended ratio hides which effect you earned &mdash; report the two factors **separately**

### The speedup did not change the answer

```{=latex}
\begin{center}
\scriptsize
\begin{tabular}{lll}
\hline
Implementation / size & Cover before $\to$ after & Cost before $\to$ after \\
\hline
Python $n=50$   & $9 \to 9$      & $49 \to 49$ \\
Python $n=100$  & $14 \to 14$    & $58 \to 58$ \\
Python $n=200$  & $25 \to 25$    & $70 \to 74$ \\
Python $n=400$  & $53 \to 58$    & $161 \to 166$ \\
C++ $n=200$     & $46 \to 46$    & $189 \to 189$ \\
Rust $n=800$    & $183 \to 183$  & $668 \to 668$ \\
\hline
\end{tabular}
\end{center}
```

C++/Rust are bit-identical; Python differs only by which odd cycle is selected &mdash; still a valid cover. The invariant $\text{dual cost} \le \text{primal cost}$ held throughout.

### Odd-cycle cover scalability

```{=latex}
\begin{center}
\footnotesize
\begin{tabular}{llll}
\hline
Impl.  & Instance     & Per-call oracle              & Speedup \\
\hline
Python & $n = 400$    & $O(V(V+E)) \to O(V+E)$       & about 200x \\
C++    & $n = 200$    & $O(V(V+E)) \to O(V+E)$       & about 28{,}800x \\
Rust   & $n = 800$    & $O(V(V+E)) \to O(V+E)$       & 12.2x \\
\hline
\end{tabular}
\end{center}
```

![Python: scaling before/after the oracle rewrite.](figures/04_scaling_python.pdf){width=31%}
![C++: scaling before/after the oracle rewrite.](figures/05_scaling_cpp.pdf){width=31%}
![Rust: scaling before/after the oracle rewrite.](figures/06_scaling_rust.pdf){width=31%}

In every case the new curve is flatter, and the gap widens with $n$ because the original oracle is super-linear.

## Conclusions

### Honest limitations, and related work

- **Real-benchmark scope:** only the covering framework is evaluated on ISPD98; Hadlock and TSP remain synthetic (no planar EDA suite offline)
- **Baselines** are the pre-existing in-house implementations, not state of the art &mdash; comparisons to Blossom V, LEMON, IP/PACE solvers, or KaHyPar are future work
- **Statistics:** single-machine, single-run wall-clock; best-of-$N$ without confidence intervals; **no new theory**
- Prior art: primal-dual for approximation [@goemans1997; @vazirani2001]; vertex cover [@baryehuda1981; @hochbaum1982]; Steiner forest [@agrawal1995]; Pitt [@pitt1985]; Christofides [@christofides1976] with blossom [@edmonds1965; @kolmogorov2009]; Hadlock [@hadlock1975]; partitioning heuristics [@kernighan1970; @fiduccia1982]

### Take-away and next steps

- Three classical techniques, developed as one story: same primitives, guarantees from three elementary facts
- Engineering is dominated by **two decisive subroutines**: a violation oracle invoked $2\lvert C \rvert$ times, and a **matching over a dense complete graph**
- Rewriting those subroutines produced speedups of **up to four orders of magnitude** &mdash; and exposed **two latent correctness bugs**
- The recurring theme: *a fast heuristic can still be wrong* &mdash; pair every optimization with an independent oracle and tests that pin the **answer**, not the runtime
- **Next:** SIMD edge processing; a **parallel, incremental reverse-delete**; honest baselines (IP, Blossom V); the **MCNC** circuits and remaining ISPD98 designs; **Rust bindings** back to Python

### Thank You

```{=latex}
\begin{center}
{\Large Questions?}\\[2mm]
{\small code: \url{https://github.com/luk036/netlistx}}
\end{center}
```

- paper: `paper/comb_optim.md`

# References {.allowframebreaks}

```{=latex}
\scriptsize
```

::: {#refs .refs}
:::
