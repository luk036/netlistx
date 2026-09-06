"""Tests for read_yosys_json and read_yosys_json_sax functions."""
import json
import tempfile
from typing import Any, Dict, Optional

from netlistx.netlist import (
    read_yosys_json,
    read_yosys_json_directed,
    read_yosys_json_sax,
)


def _make_yosys_json(
    cells: Dict[str, Dict[str, Any]],
    ports: Dict[str, Dict[str, Any]],
    netnames: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """Create a temporary Yosys JSON file and return its path."""
    data: Dict[str, Any] = {
        "modules": {
            "top": {
                "cells": cells,
                "ports": ports,
            }
        }
    }
    if netnames:
        data["modules"]["top"]["netnames"] = netnames  # type: ignore[assignment]

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, tmp)
    tmp.close()
    return tmp.name


def test_simple_and_gate() -> None:
    """Test parsing a minimal Yosys JSON with one AND gate and three ports."""
    cells = {
        "and1": {
            "type": "$and",
            "connections": {
                "A": [0],
                "B": [1],
                "Y": [2],
            },
        }
    }
    ports = {
        "a": {"direction": "input", "bits": [0]},
        "b": {"direction": "input", "bits": [1]},
        "y": {"direction": "output", "bits": [2]},
    }
    netnames = {
        "net_a": {"bits": [0]},
        "net_b": {"bits": [1]},
        "net_y": {"bits": [2]},
    }

    path = _make_yosys_json(cells, ports, netnames)
    try:
        netlist = read_yosys_json(path)

        assert netlist.number_of_modules() == 4  # 1 cell + 3 ports
        assert netlist.number_of_nets() == 3
        assert netlist.number_of_nodes() == 7  # 4 modules + 3 nets
        assert netlist.number_of_pins() == 6  # 3 cell-nets + 3 port-nets
        assert netlist.num_pads == 3  # 3 I/O ports

        assert netlist.get_module_weight(0) == 1  # cells have weight 1
        for port_idx in range(1, 4):
            assert netlist.get_module_weight(port_idx) == 0  # ports have weight 0

        assert netlist.module_fixed == {4, 5, 6}  # port nodes are fixed
    finally:
        import os

        os.unlink(path)


def test_two_cells_with_shared_net() -> None:
    """Test two cells sharing a common net."""
    cells = {
        "inv1": {
            "type": "$_INV_",
            "connections": {"A": [0], "Y": [1]},
        },
        "inv2": {
            "type": "$_INV_",
            "connections": {"A": [1], "Y": [2]},
        },
    }
    ports = {
        "in": {"direction": "input", "bits": [0]},
        "out": {"direction": "output", "bits": [2]},
    }

    path = _make_yosys_json(cells, ports)
    try:
        netlist = read_yosys_json(path)

        assert netlist.number_of_modules() == 4  # 2 cells + 2 ports
        assert netlist.number_of_nets() == 3  # nets 0, 1, 2
        assert netlist.num_pads == 2
        assert netlist.number_of_nodes() == 7  # 4 + 3
    finally:
        import os

        os.unlink(path)


def test_ignores_string_constant_nets() -> None:
    """String-valued net IDs (constants like "0", "1") should be ignored."""
    cells = {
        "and1": {
            "type": "$and",
            "connections": {
                "A": [0],
                "B": [1],
                "Y": [2],
            },
        },
        "const1": {
            "type": "$const",
            "connections": {
                "Y": [0],
                "A": ["0", "0", "0", "0"],
            },
        },
    }
    ports = {
        "a": {"direction": "input", "bits": [0]},
        "b": {"direction": "input", "bits": [1]},
        "y": {"direction": "output", "bits": [2]},
    }

    path = _make_yosys_json(cells, ports)
    try:
        netlist = read_yosys_json(path)

        # 2 cells + 3 ports = 5 modules
        assert netlist.number_of_modules() == 5
        # 3 distinct integer nets (string "0" constants excluded)
        assert netlist.number_of_nets() == 3
    finally:
        import os

        os.unlink(path)


def test_no_netnames() -> None:
    """Test Yosys JSON without netnames section (nets come from ports + cells only)."""
    cells = {
        "buf1": {
            "type": "$buf",
            "connections": {
                "A": [0],
                "Y": [1],
            },
        }
    }
    ports = {
        "in": {"direction": "input", "bits": [0]},
        "out": {"direction": "output", "bits": [1]},
    }

    path = _make_yosys_json(cells, ports)
    try:
        netlist = read_yosys_json(path)
        assert netlist.number_of_modules() == 3  # 1 cell + 2 ports
        assert netlist.number_of_nets() == 2
        assert netlist.num_pads == 2
    finally:
        import os

        os.unlink(path)


# ── SAX parser tests (mirror the DOM tests) ────────────────────────


def test_sax_simple_and_gate() -> None:
    cells = {
        "and1": {
            "type": "$and",
            "connections": {
                "A": [0],
                "B": [1],
                "Y": [2],
            },
        }
    }
    ports = {
        "a": {"direction": "input", "bits": [0]},
        "b": {"direction": "input", "bits": [1]},
        "y": {"direction": "output", "bits": [2]},
    }
    netnames = {
        "net_a": {"bits": [0]},
        "net_b": {"bits": [1]},
        "net_y": {"bits": [2]},
    }

    path = _make_yosys_json(cells, ports, netnames)
    try:
        netlist = read_yosys_json_sax(path)

        assert netlist.number_of_modules() == 4
        assert netlist.number_of_nets() == 3
        assert netlist.number_of_nodes() == 7
        assert netlist.number_of_pins() == 6
        assert netlist.num_pads == 3

        assert netlist.get_module_weight(0) == 1
        for port_idx in range(1, 4):
            assert netlist.get_module_weight(port_idx) == 0

        assert netlist.module_fixed == {4, 5, 6}
    finally:
        import os

        os.unlink(path)


def test_sax_two_cells_with_shared_net() -> None:
    cells = {
        "inv1": {
            "type": "$_INV_",
            "connections": {"A": [0], "Y": [1]},
        },
        "inv2": {
            "type": "$_INV_",
            "connections": {"A": [1], "Y": [2]},
        },
    }
    ports = {
        "in": {"direction": "input", "bits": [0]},
        "out": {"direction": "output", "bits": [2]},
    }

    path = _make_yosys_json(cells, ports)
    try:
        netlist = read_yosys_json_sax(path)

        assert netlist.number_of_modules() == 4
        assert netlist.number_of_nets() == 3
        assert netlist.num_pads == 2
        assert netlist.number_of_nodes() == 7
    finally:
        import os

        os.unlink(path)


def test_sax_ignores_string_constant_nets() -> None:
    cells = {
        "and1": {
            "type": "$and",
            "connections": {
                "A": [0],
                "B": [1],
                "Y": [2],
            },
        },
        "const1": {
            "type": "$const",
            "connections": {
                "Y": [0],
                "A": ["0", "0", "0", "0"],
            },
        },
    }
    ports = {
        "a": {"direction": "input", "bits": [0]},
        "b": {"direction": "input", "bits": [1]},
        "y": {"direction": "output", "bits": [2]},
    }

    path = _make_yosys_json(cells, ports)
    try:
        netlist = read_yosys_json_sax(path)

        assert netlist.number_of_modules() == 5
        assert netlist.number_of_nets() == 3
    finally:
        import os

        os.unlink(path)


def test_sax_no_netnames() -> None:
    cells = {
        "buf1": {
            "type": "$buf",
            "connections": {
                "A": [0],
                "Y": [1],
            },
        }
    }
    ports = {
        "in": {"direction": "input", "bits": [0]},
        "out": {"direction": "output", "bits": [1]},
    }

    path = _make_yosys_json(cells, ports)
    try:
        netlist = read_yosys_json_sax(path)
        assert netlist.number_of_modules() == 3
        assert netlist.number_of_nets() == 2
        assert netlist.num_pads == 2
    finally:
        import os

        os.unlink(path)


# ── Cross-validation: DOM vs SAX produce identical results ────────


def test_dom_sax_identical_small() -> None:
    """Both parsers must produce identical Netlists for the same input."""
    cells = {
        "and1": {
            "type": "$and",
            "connections": {"A": [0], "B": [1], "Y": [2]},
        },
        "or1": {
            "type": "$or",
            "connections": {"A": [3], "B": [4], "Y": [5]},
        },
        "xor1": {
            "type": "$xor",
            "connections": {"A": [2], "B": [5], "Y": [6]},
        },
    }
    ports = {
        "a": {"direction": "input", "bits": [0]},
        "b": {"direction": "input", "bits": [1]},
        "c": {"direction": "input", "bits": [3]},
        "d": {"direction": "input", "bits": [4]},
        "out": {"direction": "output", "bits": [6]},
    }
    netnames = {
        "net_a": {"bits": [0]},
        "net_b": {"bits": [1]},
        "net_and_out": {"bits": [2]},
        "net_c": {"bits": [3]},
        "net_d": {"bits": [4]},
        "net_or_out": {"bits": [5]},
        "net_out": {"bits": [6]},
    }

    path = _make_yosys_json(cells, ports, netnames)
    try:
        dom = read_yosys_json(path)
        sax = read_yosys_json_sax(path)

        assert dom.number_of_modules() == sax.number_of_modules()
        assert dom.number_of_nets() == sax.number_of_nets()
        assert dom.number_of_nodes() == sax.number_of_nodes()
        assert dom.number_of_pins() == sax.number_of_pins()
        assert dom.num_pads == sax.num_pads
        assert dom.module_fixed == sax.module_fixed

        for i in range(dom.number_of_modules()):
            assert dom.get_module_weight(i) == sax.get_module_weight(i)
    finally:
        import os

        os.unlink(path)


def test_dom_sax_identical_sphere_netlist() -> None:
    """Both parsers must produce identical results for sphere_netlist.json."""
    path = "yosys_testcases/sphere_netlist.json"
    dom = read_yosys_json(path)
    sax = read_yosys_json_sax(path)

    assert dom.number_of_modules() == sax.number_of_modules()
    assert dom.number_of_nets() == sax.number_of_nets()
    assert dom.number_of_nodes() == sax.number_of_nodes()
    assert dom.number_of_pins() == sax.number_of_pins()
    assert dom.num_pads == sax.num_pads
    assert dom.module_fixed == sax.module_fixed

    for i in range(dom.number_of_modules()):
        assert dom.get_module_weight(i) == sax.get_module_weight(i)


def test_dom_sax_identical_sphere3hopf() -> None:
    """Both parsers must produce identical results for sphere3hopf_netlist_simple.json."""
    path = "yosys_testcases/sphere3hopf_netlist_simple.json"
    dom = read_yosys_json(path)
    sax = read_yosys_json_sax(path)

    assert dom.number_of_modules() == sax.number_of_modules()
    assert dom.number_of_nets() == sax.number_of_nets()
    assert dom.number_of_nodes() == sax.number_of_nodes()
    assert dom.number_of_pins() == sax.number_of_pins()
    assert dom.num_pads == sax.num_pads
    assert dom.module_fixed == sax.module_fixed

    for i in range(dom.number_of_modules()):
        assert dom.get_module_weight(i) == sax.get_module_weight(i)

def test_directed_driver_net_identity() -> None:
    """The directed reader must identify the driver module of every net."""
    cells = {
        "and1": {
            "type": "$and",
            "port_directions": {"A": "input", "B": "input", "Y": "output"},
            "connections": {"A": [0], "B": [1], "Y": [2]},
        }
    }
    ports = {
        "a": {"direction": "input", "bits": [0]},
        "b": {"direction": "input", "bits": [1]},
        "y": {"direction": "output", "bits": [2]},
    }
    netnames = {"net_a": {"bits": [0]}, "net_b": {"bits": [1]}, "net_y": {"bits": [2]}}

    path = _make_yosys_json(cells, ports, netnames)
    try:
        netlist = read_yosys_json_directed(path)
        driver = netlist.net_driver
        assert driver[1] == 4  # net 0 (input a) is driven by pad node 4
        assert driver[2] == 5  # net 1 (input b) is driven by pad node 5
        assert driver[3] == 0  # net 2 (output y) is driven by cell 0 (Y output)
    finally:
        import os

        os.unlink(path)


def test_directed_sphere3hopf_every_net_has_driver() -> None:
    """Every net of the Yosys benchmark must have exactly one driver."""
    path = "yosys_testcases/sphere3hopf_netlist_simple.json"
    netlist = read_yosys_json_directed(path)
    driver = netlist.net_driver
    assert len(driver) == netlist.number_of_nets()
    module_ids = set(netlist.modules)
    assert all(v in module_ids for v in driver.values())
    assert any(v is None for v in driver.values()) is False
