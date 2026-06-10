"""Targeted tests to cover uncovered lines in readwrite.py.

Missing lines: [38, 41, 73, 76]
Missing branches: [[37, 38], [40, 41], [72, 73], [75, 76]]
"""

import os
import tempfile

from netlistx.readwrite import read_are, read_netd


class TestReadNetdEdgeCases:
    """Cover lines 38 (early break) and 41 (empty lines)."""

    def _make_net_file(self, lines):
        """Create a temp .net file with given lines."""
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".net", delete=False)
        tmp.writelines(lines)
        tmp.close()
        return tmp.name

    def test_early_break_pin_count(self) -> None:
        """Trigger line 38 break when pin_count >= numPins.

        Declare 1 pin but provide more entries - should break early.
        """
        content = [
            "0\n",      # dummy line 0
            "1\n",      # 1 pin
            "1\n",      # 1 net
            "2\n",      # 2 modules
            "0\n",      # pad offset 0
            "a0 s 0\n",  # first entry
            "a1 l 0\n",  # second entry (should trigger break)
        ]
        path = self._make_net_file(content)
        try:
            netlist = read_netd(path)
            assert netlist is not None
        finally:
            os.unlink(path)

    def test_empty_lines_in_file(self) -> None:
        """Trigger line 41 continue when line is empty."""
        content = [
            "0\n",
            "1\n",
            "1\n",
            "2\n",
            "0\n",
            "\n",          # empty line → continue
            "a0 s 0\n",    # first pin entry
        ]
        path = self._make_net_file(content)
        try:
            netlist = read_netd(path)
            assert netlist is not None
        finally:
            os.unlink(path)

    def test_empty_line_between_entries(self) -> None:
        """Multiple empty lines and normal entries mixed."""
        content = [
            "0\n",
            "2\n",
            "2\n",
            "3\n",
            "0\n",
            "a0 s 0\n",
            "\n",
            "a1 l 0\n",
            "\n",
            "p0 s 1\n",
        ]
        path = self._make_net_file(content)
        try:
            netlist = read_netd(path)
            assert netlist is not None
        finally:
            os.unlink(path)


class TestReadAreEdgeCases:
    """Cover lines 73 (empty lines) and 76 (short lines)."""

    def _make_are_file(self, lines):
        """Create a temp .are file with given lines."""
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".are", delete=False)
        tmp.writelines(lines)
        tmp.close()
        return tmp.name

    def test_empty_line_in_are(self) -> None:
        """Trigger line 73 continue when line is empty."""
        content = [
            "a0 10\n",
            "\n",        # empty line → continue
            "a1 20\n",
        ]
        are_path = self._make_are_file(content)

        # Need a netlist to pass in - use a minimal one
        tmp_net_path = None
        try:
            net_content = [
                "0\n",
                "2\n",
                "2\n",
                "3\n",
                "0\n",
                "a0 s 0\n",
                "a1 l 0\n",
            ]
            tmp_net = tempfile.NamedTemporaryFile(
                mode="w", suffix=".net", delete=False
            )
            tmp_net.writelines(net_content)
            tmp_net.close()
            tmp_net_path = tmp_net.name

            netlist = read_netd(tmp_net_path)
            read_are(netlist, are_path)
            assert netlist.get_module_weight(0) == 10
            assert netlist.get_module_weight(1) == 20
        finally:
            if tmp_net_path:
                os.unlink(tmp_net_path)
            os.unlink(are_path)

    def test_short_line_in_are(self) -> None:
        """Trigger line 76 continue when line has fewer than 2 parts."""
        content = [
            "a0 10\n",
            "invalid_no_weight\n",  # < 2 parts → continue
            "a1 20\n",
        ]
        are_path = self._make_are_file(content)

        tmp_net_path = None
        try:
            net_content = [
                "0\n",
                "2\n",
                "2\n",
                "3\n",
                "0\n",
                "a0 s 0\n",
                "a1 l 0\n",
            ]
            tmp_net = tempfile.NamedTemporaryFile(
                mode="w", suffix=".net", delete=False
            )
            tmp_net.writelines(net_content)
            tmp_net.close()
            tmp_net_path = tmp_net.name

            netlist = read_netd(tmp_net_path)
            read_are(netlist, are_path)
            assert netlist.get_module_weight(0) == 10
            assert netlist.get_module_weight(1) == 20
        finally:
            if tmp_net_path:
                os.unlink(tmp_net_path)
            os.unlink(are_path)
