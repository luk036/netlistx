"""Benchmark comparison: read_yosys_json (DOM) vs read_yosys_json_sax (SAX).

Pytest-benchmark fixtures are injected by ``pytest-benchmark``.
Run with: ``pytest benches/test_bm_yosys.py --benchmark-only``
"""
from typing import Any

from netlistx.netlist import read_yosys_json, read_yosys_json_sax

SPHERE_PATH = "yosys_testcases/sphere_netlist.json"
SPHERE3HOPF_PATH = "yosys_testcases/sphere3hopf_netlist_simple.json"


def test_dom_sphere(benchmark: Any) -> None:
    """DOM (json.load) — 482 KB sphere netlist."""
    netlist = benchmark(read_yosys_json, SPHERE_PATH)
    assert netlist.number_of_modules() > 0
    assert netlist.number_of_nets() > 0


def test_sax_sphere(benchmark: Any) -> None:
    """SAX (ijson) — 482 KB sphere netlist."""
    netlist = benchmark(read_yosys_json_sax, SPHERE_PATH)
    assert netlist.number_of_modules() > 0
    assert netlist.number_of_nets() > 0


def test_dom_sphere3hopf(benchmark: Any) -> None:
    """DOM (json.load) — 528 KB sphere3hopf netlist."""
    netlist = benchmark(read_yosys_json, SPHERE3HOPF_PATH)
    assert netlist.number_of_modules() > 0
    assert netlist.number_of_nets() > 0


def test_sax_sphere3hopf(benchmark: Any) -> None:
    """SAX (ijson) — 528 KB sphere3hopf netlist."""
    netlist = benchmark(read_yosys_json_sax, SPHERE3HOPF_PATH)
    assert netlist.number_of_modules() > 0
    assert netlist.number_of_nets() > 0
