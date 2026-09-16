"""Generate standalone SVG figures for the minimum odd cycle cover work.

The figures illustrate two things:

1. The problem itself - what a minimum odd cycle cover is (even vs. odd
   cycles, and which vertices a cover picks).
2. The runtime issue found in the primal-dual violation oracle, the fix that
   was applied to the Python / C++ / Rust ports, and the measured speedups.

The concept covers are computed with the real ``netlistx`` implementation so
the pictures are truthful rather than hand-drawn.

Usage::

    python figures/generate_figures.py

Writes ``*.svg`` next to this file.
"""

from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if os.path.isdir(os.path.join(ROOT, "src")):
    sys.path.insert(0, os.path.join(ROOT, "src"))

import networkx as nx  # noqa: E402

from netlistx.cover import min_odd_cycle_cover  # noqa: E402

INK = "#1b2631"
MUTED = "#5d6d7e"
FAINT = "#98a6ad"
GRID = "#e8ebed"
PANEL = "#fbfcfd"
PANEL_STROKE = "#d5dbdf"
NODE = "#d4e6f1"
NODE_STROKE = "#2c3e50"
COVER = "#f5b7b1"
COVER_STROKE = "#c0392b"
COLOR_A = "#aed6f1"
COLOR_B = "#f9e79f"
COLOR_A_STROKE = "#1f618d"
COLOR_B_STROKE = "#b7950b"
EDGE = "#95a5a6"
BEFORE = "#c0392b"
AFTER = "#1e8449"
RUST_C = "#b9770e"
CPP_C = "#2471a3"
PY_C = "#7d3c98"
FONT = "Segoe UI, Helvetica, Arial, sans-serif"


def esc(body: str) -> str:
    return body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(
    x: float,
    y: float,
    body: str,
    *,
    size: float = 14,
    anchor: str = "middle",
    fill: str = INK,
    weight: str = "normal",
    rotate: float | None = None,
) -> str:
    transform = (
        f' transform="rotate({rotate} {x:.1f} {y:.1f})"' if rotate is not None else ""
    )
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
        f'fill="{fill}" font-weight="{weight}"{transform}>{esc(body)}</text>'
    )


def circle(
    cx: float, cy: float, r: float, *, fill: str, stroke: str, sw: float = 2.0
) -> str:
    return (
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{sw}"/>'
    )


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    stroke: str = EDGE,
    sw: float = 2.0,
    dash: str | None = None,
    arrow: bool = False,
) -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    a = ' marker-end="url(#arrow)"' if arrow else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"{d}{a}/>'
    )


def rect(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str,
    stroke: str = "none",
    sw: float = 1.0,
    rx: float = 0.0,
) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    )


def polyline(points: list[tuple[float, float]], *, stroke: str, sw: float = 2.5) -> str:
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return (
        f'<polyline points="{pts}" fill="none" stroke="{stroke}" '
        f'stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"/>'
    )


def graph_node(
    cx: float,
    cy: float,
    label: str,
    *,
    fill: str = NODE,
    stroke: str = NODE_STROKE,
    r: float = 19.0,
    sw: float = 2.0,
    tsize: float = 13.0,
) -> str:
    return circle(cx, cy, r, fill=fill, stroke=stroke, sw=sw) + text(
        cx, cy + tsize * 0.36, label, size=tsize, weight="bold"
    )


def svg_open(w: float, h: float, title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
        f'viewBox="0 0 {w:.0f} {h:.0f}" font-family="{FONT}">\n'
        f"<title>{esc(title)}</title>\n"
        f'<rect width="{w:.0f}" height="{h:.0f}" fill="#ffffff"/>\n'
        f"<defs>\n"
        f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker>\n'
        f"</defs>\n"
    )


def panel(x: float, y: float, w: float, h: float, title: str) -> str:
    return rect(x, y, w, h, fill=PANEL, stroke=PANEL_STROKE, sw=1.5, rx=10) + text(
        x + 18, y + 30, title, size=15, anchor="start", weight="bold"
    )


def banner(w: float, title: str, subtitle: str) -> str:
    return text(w / 2, 34, title, size=21, weight="bold") + text(
        w / 2, 58, subtitle, size=13, fill=MUTED
    )


def write_svg(name: str, body: str) -> str:
    path = os.path.join(HERE, name)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return path


def odd_cycle_cover(edges: list[tuple[int, int]]) -> tuple[set[int], int]:
    grph = nx.Graph()
    grph.add_edges_from(edges)
    weight = {v: 1 for v in grph.nodes()}
    cover, cost = min_odd_cycle_cover(grph, weight, set())
    return set(cover), cost


def figure_even_vs_odd() -> str:
    w, h = 940, 430
    out = [svg_open(w, h, "Even vs. odd cycle and the odd cycle cover")]
    out.append(
        banner(
            w,
            "Even cycles need nothing, odd cycles need one vertex",
            "C is an odd cycle cover iff G[V \\ C] has no odd cycle, i.e. is bipartite",
        )
    )

    out.append(panel(30, 80, 420, 320, "(a)  Even cycle C4 - bipartite"))
    square = [(0, 1), (1, 2), (2, 3), (3, 0)]
    _, square_cost = odd_cycle_cover(square)
    pos_square = {0: (140, 180), 1: (310, 180), 2: (310, 320), 3: (140, 320)}
    for u, v in square:
        out.append(line(*pos_square[u], *pos_square[v], stroke=EDGE, sw=2.5))
    for node, (cx, cy) in pos_square.items():
        out.append(graph_node(cx, cy, f"n{node}"))
    out.append(
        text(225, 372, "2-colourable, so no odd cycle exists", size=13, fill=MUTED)
    )
    out.append(
        text(
            225,
            393,
            f"cover = {{}}   cost = {square_cost}",
            size=14,
            weight="bold",
            fill=AFTER,
        )
    )

    out.append(panel(490, 80, 420, 320, "(b)  Odd cycle C3 - non-bipartite"))
    triangle = [(4, 5), (5, 6), (6, 4)]
    tri_cover, tri_cost = odd_cycle_cover(triangle)
    pos_tri = {4: (700, 175), 5: (605, 315), 6: (795, 315)}
    for u, v in triangle:
        out.append(line(*pos_tri[u], *pos_tri[v], stroke=EDGE, sw=2.5))
    for node, (cx, cy) in pos_tri.items():
        chosen = node in tri_cover
        out.append(
            graph_node(
                cx,
                cy,
                f"n{node}",
                fill=COVER if chosen else NODE,
                stroke=COVER_STROKE if chosen else NODE_STROKE,
                sw=3.0 if chosen else 2.0,
            )
        )
    out.append(
        text(700, 372, "one vertex breaks the only odd cycle", size=13, fill=MUTED)
    )
    names = ", ".join(f"n{v}" for v in sorted(tri_cover))
    out.append(
        text(
            700,
            393,
            f"cover = {{{names}}}   cost = {tri_cost}",
            size=14,
            weight="bold",
            fill=BEFORE,
        )
    )

    out.append("</svg>\n")
    return "".join(out)


def figure_cover_mixed() -> str:
    w, h = 940, 480
    out = [svg_open(w, h, "Odd cycle cover of a mixed graph")]
    out.append(
        banner(
            w,
            "The cover touches only the odd cycle",
            "Square n0-n3 (even) plus triangle n4-n6 (odd); the square is left untouched",
        )
    )

    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 4)]
    cover, cost = odd_cycle_cover(edges)
    pos = {
        0: (150, 150),
        1: (300, 150),
        2: (300, 290),
        3: (150, 290),
        4: (660, 140),
        5: (560, 300),
        6: (760, 300),
    }
    for u, v in edges:
        odd_edge = u >= 4 and v >= 4
        out.append(
            line(
                *pos[u],
                *pos[v],
                stroke=BEFORE if odd_edge else EDGE,
                sw=3.0 if odd_edge else 2.0,
                dash=None if odd_edge else "6 5",
            )
        )
    for node, (cx, cy) in pos.items():
        chosen = node in cover
        out.append(
            graph_node(
                cx,
                cy,
                f"n{node}",
                fill=COVER if chosen else NODE,
                stroke=COVER_STROKE if chosen else NODE_STROKE,
                sw=3.0 if chosen else 2.0,
            )
        )

    out.append(text(225, 355, "even cycle", size=14, fill=MUTED, weight="bold"))
    out.append(text(225, 376, "no vertex selected", size=12, fill=FAINT))
    out.append(text(660, 355, "odd cycle", size=14, fill=BEFORE, weight="bold"))
    out.append(text(660, 376, "one vertex selected", size=12, fill=FAINT))

    out.append(rect(120, 405, 700, 50, fill=PANEL, stroke=PANEL_STROKE, sw=1.5, rx=8))
    names = ", ".join(f"n{v}" for v in sorted(cover))
    out.append(
        text(
            470,
            436,
            f"min_odd_cycle_cover  ->  {{{names}}},  cost = {cost}",
            size=15,
            weight="bold",
        )
    )

    out.append("</svg>\n")
    return "".join(out)


def _mini_graph(
    cx: float, cy: float, scale: float, colors: list[str] | None = None
) -> str:
    pts = [
        (cx - 62 * scale, cy - 56 * scale),
        (cx + 62 * scale, cy - 56 * scale),
        (cx + 62 * scale, cy + 56 * scale),
        (cx - 62 * scale, cy + 56 * scale),
        (cx, cy),
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
    body = [line(*pts[u], *pts[v], stroke=EDGE, sw=2.0) for u, v in edges]
    for idx, (px, py) in enumerate(pts):
        fill = colors[idx] if colors else NODE
        stroke = NODE_STROKE
        if colors:
            stroke = COLOR_A_STROKE if colors[idx] == COLOR_A else COLOR_B_STROKE
        body.append(
            graph_node(px, py, "", fill=fill, stroke=stroke, r=13 * scale, sw=2.0)
        )
    return "".join(body)


def figure_oracle() -> str:
    w, h = 960, 470
    out = [svg_open(w, h, "Primal-dual violation oracle: before and after")]
    out.append(
        banner(
            w,
            "The violation oracle dominated the runtime",
            "pd_cover calls the oracle about 2x|cover| times, and the old oracle restarted a full search each call",
        )
    )

    out.append(panel(30, 80, 430, 360, "BEFORE - super-linear per call"))
    out.append(_mini_graph(148, 195, 0.78))
    out.append(text(340, 160, "5 BFS passes", size=12, fill=MUTED))
    for i in range(5):
        chip_x = 288 + i * 30
        out.append(
            rect(chip_x, 175, 24, 24, fill="#fdf2f1", stroke="#e6b0aa", sw=1.4, rx=5)
        )
        out.append(
            text(chip_x + 12, 192, str(i + 1), size=12, fill=BEFORE, weight="bold")
        )
    out.append(
        text(245, 266, "BFS restarted from every source,", size=12.5, fill=MUTED)
    )
    out.append(
        text(245, 288, "topology recomputed on every call", size=12.5, fill=MUTED)
    )
    out.append(rect(50, 312, 390, 113, fill="#fdf2f1", stroke="#e6b0aa", sw=1.5, rx=8))
    out.append(
        text(
            245,
            340,
            "cost per call:  O(V x (V + E))",
            size=16,
            weight="bold",
            fill=BEFORE,
        )
    )
    out.append(
        text(
            245,
            366,
            "Python: BCC + chain decomposition, BFS per source",
            size=11.5,
            fill=MUTED,
        )
    )
    out.append(
        text(
            245,
            386,
            "C++: materialises every cycle, copying BFS info",
            size=11.5,
            fill=MUTED,
        )
    )
    out.append(
        text(
            245,
            406,
            "Rust: O(V) node-name scan per dequeued node",
            size=11.5,
            fill=MUTED,
        )
    )

    out.append(panel(500, 80, 430, 360, "AFTER - single linear pass"))
    out.append(
        _mini_graph(
            620, 205, 0.82, colors=[COLOR_A, COLOR_B, COLOR_A, COLOR_B, COLOR_A]
        )
    )
    out.append(line(700, 205, 750, 205, stroke=MUTED, sw=2.0, arrow=True))
    out.append(text(758, 195, "first same-colour", size=12, fill=MUTED, anchor="start"))
    out.append(text(758, 213, "edge = odd cycle", size=12, fill=MUTED, anchor="start"))
    out.append(rect(520, 300, 390, 122, fill="#f0f9f3", stroke="#a9dfbf", sw=1.5, rx=8))
    out.append(
        text(715, 328, "cost per call:  O(V + E)", size=16, weight="bold", fill=AFTER)
    )
    out.append(
        text(
            715,
            354,
            "one BFS 2-colouring; a same-colour edge closes an odd cycle",
            size=11.5,
            fill=MUTED,
        )
    )
    out.append(
        text(
            715,
            374,
            "all three ports return the first odd cycle directly",
            size=11.5,
            fill=MUTED,
        )
    )
    out.append(
        text(
            715,
            394,
            "same cover size and cost, unchanged semantics",
            size=11.5,
            fill=MUTED,
        )
    )

    out.append("</svg>\n")
    return "".join(out)


PY_DATA = {
    "name": "Python (netlistx)",
    "color": PY_C,
    "x": [50, 100, 200, 400],
    "before": [106.7, 296.8, 1503.4, 9506.6],
    "after": [1.1973, 2.8585, 10.9761, 46.7344],
}
CPP_DATA = {
    "name": "C++ (xnetwork-cpp)",
    "color": CPP_C,
    "x": [100, 200, 400, 800],
    "before": [6846.84, 126123.0, None, None],
    "after": [1.3952, 4.3743, 16.169, 54.57],
}
RUST_DATA = {
    "name": "Rust (netlistx-rs)",
    "color": RUST_C,
    "x": [100, 200, 400, 800],
    "before": [4.8629, 19.3516, 75.329, 381.7599],
    "after": [0.9434, 2.9225, 8.0435, 31.3197],
}


def _log_bounds(values: list[float]) -> tuple[float, float]:
    lo = 10 ** math.floor(math.log10(min(values)))
    hi = 10 ** math.ceil(math.log10(max(values)))
    return lo, hi


def _fmt_ms(value: float) -> str:
    return f"{value:,.0f}" if value >= 100 else f"{value:.2f}"


def scaling_chart(data: dict, *, note: str | None = None) -> str:
    w, h = 780, 470
    left, right, top, bottom = 118, w - 45, 112, h - 80
    plot_w, plot_h = right - left, bottom - top
    values = [v for v in data["before"] + data["after"] if v is not None]
    lo, hi = _log_bounds(values)
    count = len(data["x"])

    def px(index: int) -> float:
        return left + plot_w * index / (count - 1)

    def py(value: float) -> float:
        frac = (math.log10(hi) - math.log10(value)) / (math.log10(hi) - math.log10(lo))
        return top + frac * plot_h

    out = [svg_open(w, h, f"Runtime scaling - {data['name']}")]
    out.append(
        banner(w, f"Odd cycle cover runtime - {data['name']}", "lower is better")
    )

    decade = lo
    while decade <= hi * 1.0001:
        y = py(decade)
        out.append(line(left, y, right, y, stroke=GRID, sw=1.0))
        out.append(
            text(left - 12, y + 4, f"{decade:,.0f}", size=12, anchor="end", fill=MUTED)
        )
        decade *= 10

    out.append(line(left, top, left, bottom, stroke=MUTED, sw=1.5))
    out.append(line(left, bottom, right, bottom, stroke=MUTED, sw=1.5))

    for idx, n in enumerate(data["x"]):
        out.append(text(px(idx), bottom + 24, f"{n}", size=12, fill=MUTED))
    out.append(text((left + right) / 2, bottom + 48, "nodes (n)", size=13, fill=INK))
    out.append(
        text(
            34,
            (top + bottom) / 2,
            "time (ms, log scale)",
            size=13,
            fill=INK,
            rotate=-90,
        )
    )

    for key, color, dy in (("before", BEFORE, 20), ("after", AFTER, -13)):
        pts = [(px(i), py(v)) for i, v in enumerate(data[key]) if v is not None]
        if len(pts) >= 2:
            out.append(polyline(pts, stroke=color, sw=3.0))
        for x, y in pts:
            out.append(circle(x, y, 5.5, fill="#ffffff", stroke=color, sw=3.0))
        for i, v in enumerate(data[key]):
            if v is None:
                continue
            anchor, dx = "middle", 0.0
            if i == 0:
                anchor, dx = "start", 7.0
            elif i == count - 1:
                anchor, dx = "end", -7.0
            out.append(
                text(
                    px(i) + dx,
                    py(v) + dy,
                    _fmt_ms(v),
                    size=11,
                    fill=color,
                    weight="bold",
                    anchor=anchor,
                )
            )

    out.append(line(left + 12, 86, left + 44, 86, stroke=BEFORE, sw=3.0))
    out.append(text(left + 52, 90, "before", size=12.5, anchor="start", fill=INK))
    out.append(line(left + 124, 86, left + 156, 86, stroke=AFTER, sw=3.0))
    out.append(text(left + 164, 90, "after", size=12.5, anchor="start", fill=INK))

    if note:
        out.append(
            rect(
                left, h - 42, plot_w, 28, fill=PANEL, stroke=PANEL_STROKE, sw=1.2, rx=6
            )
        )
        out.append(text(left + plot_w / 2, h - 23, note, size=11.5, fill=MUTED))

    out.append("</svg>\n")
    return "".join(out)


def speedup_chart() -> str:
    w, h = 800, 470
    left, right, top, bottom = 118, w - 45, 118, h - 80
    plot_w, plot_h = right - left, bottom - top

    series = []
    all_n: list[int] = []
    for data in (PY_DATA, CPP_DATA, RUST_DATA):
        ratios = [
            (n, before / after)
            for n, before, after in zip(data["x"], data["before"], data["after"])
            if before is not None and after
        ]
        series.append((data["name"], data["color"], ratios))
        all_n.extend(n for n, _ in ratios)

    x_lo = 10 ** math.floor(math.log10(min(all_n)))
    x_hi = 10 ** math.ceil(math.log10(max(all_n)))
    y_hi = 10 ** math.ceil(math.log10(max(v for _, _, r in series for _, v in r)))
    y_lo = 1.0

    def px(n: int) -> float:
        frac = (math.log10(n) - math.log10(x_lo)) / (
            math.log10(x_hi) - math.log10(x_lo)
        )
        return left + frac * plot_w

    def py(value: float) -> float:
        frac = (math.log10(value) - math.log10(y_lo)) / (
            math.log10(y_hi) - math.log10(y_lo)
        )
        return bottom - frac * plot_h

    out = [svg_open(w, h, "Speedup by input size")]
    out.append(
        banner(
            w,
            "Measured speedup of the new oracle",
            "identical cover size and cost in every case; higher is better",
        )
    )

    decade = y_lo
    while decade <= y_hi * 1.0001:
        y = py(decade)
        out.append(line(left, y, right, y, stroke=GRID, sw=1.0))
        out.append(
            text(left - 12, y + 4, f"{decade:g}x", size=12, anchor="end", fill=MUTED)
        )
        decade *= 10

    out.append(line(left, top, left, bottom, stroke=MUTED, sw=1.5))
    out.append(line(left, bottom, right, bottom, stroke=MUTED, sw=1.5))

    for n in (50, 100, 200, 400, 800):
        if x_lo <= n <= x_hi:
            out.append(line(px(n), bottom, px(n), bottom + 5, stroke=MUTED, sw=1.2))
            out.append(text(px(n), bottom + 24, f"{n}", size=12, fill=MUTED))
    out.append(
        text((left + right) / 2, bottom + 48, "nodes (n, log scale)", size=13, fill=INK)
    )
    out.append(text(34, (top + bottom) / 2, "speedup", size=13, fill=INK, rotate=-90))

    for name, color, ratios in series:
        pts = [(px(n), py(v)) for n, v in ratios]
        if len(pts) >= 2:
            out.append(polyline(pts, stroke=color, sw=3.0))
        for (mx, my), (_, v) in zip(pts, ratios):
            out.append(circle(mx, my, 5.5, fill="#ffffff", stroke=color, sw=3.0))
            out.append(
                text(mx, my - 13, f"{v:,.0f}x", size=11, fill=color, weight="bold")
            )

    lx = left
    for name, color, _ in series:
        out.append(line(lx, 92, lx + 30, 92, stroke=color, sw=3.0))
        out.append(text(lx + 38, 96, name, size=12, anchor="start", fill=INK))
        lx += 38 + 6.6 * len(name) + 26

    out.append("</svg>\n")
    return "".join(out)


def main() -> None:
    figures = {
        "01_even_vs_odd_cycle.svg": figure_even_vs_odd(),
        "02_odd_cycle_cover_mixed.svg": figure_cover_mixed(),
        "03_oracle_before_after.svg": figure_oracle(),
        "04_scaling_python.svg": scaling_chart(PY_DATA),
        "05_scaling_cpp.svg": scaling_chart(
            CPP_DATA, note="C++ 'before' at n=400 did not finish within a 20-minute cap"
        ),
        "06_scaling_rust.svg": scaling_chart(RUST_DATA),
        "07_speedup_summary.svg": speedup_chart(),
    }
    for name, body in figures.items():
        print(f"wrote {write_svg(name, body)}")


if __name__ == "__main__":
    main()
