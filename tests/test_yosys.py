"""Tests for read_yosys_json function."""
import json
import tempfile
from typing import Any, Dict, Optional

from netlistx.netlist import read_yosys_json


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
