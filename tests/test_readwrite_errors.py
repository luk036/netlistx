"""Error-path tests for the readwrite module."""

import json

import pytest

from netlistx.readwrite import read_json, read_netd, read_yosys_json, read_yosys_json_directed


def test_read_netd_missing_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        read_netd(str(tmp_path / "missing.net"))


def test_read_netd_truncated_header(tmp_path) -> None:
    path = tmp_path / "short.net"
    path.write_text("0\n1\n1\n")
    with pytest.raises(ValueError, match="5-line header"):
        read_netd(str(path))


def test_read_json_missing_metadata(tmp_path) -> None:
    path = tmp_path / "graph.json"
    path.write_text(
        json.dumps(
            {
                "directed": False,
                "multigraph": False,
                "nodes": [{"id": 0}, {"id": 1}],
                "edges": [{"source": 0, "target": 1}],
            }
        )
    )
    with pytest.raises(ValueError, match="missing required metadata"):
        read_json(str(path))


def test_read_yosys_json_missing_modules(tmp_path) -> None:
    path = tmp_path / "yosys.json"
    path.write_text(json.dumps({"creator": "Yosys"}))
    with pytest.raises(ValueError, match="no 'modules'"):
        read_yosys_json(str(path))


def test_read_yosys_json_empty_modules(tmp_path) -> None:
    path = tmp_path / "yosys.json"
    path.write_text(json.dumps({"modules": {}}))
    with pytest.raises(ValueError, match="no 'modules'"):
        read_yosys_json(str(path))


def test_read_yosys_json_directed_missing_modules(tmp_path) -> None:
    path = tmp_path / "yosys.json"
    path.write_text(json.dumps({"modules": {}}))
    with pytest.raises(ValueError, match="no 'modules'"):
        read_yosys_json_directed(str(path))


def test_read_yosys_json_missing_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        read_yosys_json(str(tmp_path / "missing.json"))
