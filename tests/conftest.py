import pytest
import json
from netlistx.netlist import create_drawf, read_json


@pytest.fixture
def drawf_graph():
    """Fixture for creating a hypergraph from the drawf file."""
    return create_drawf()


@pytest.fixture
def p1_graph():
    """Fixture for creating a hypergraph from the p1.json file."""
    return read_json("testcases/p1.json")


@pytest.fixture
def drawf_json():
    """Fixture for loading the drawf.json file."""
    with open("testcases/drawf.json", "r") as fr:
        return json.load(fr)


@pytest.fixture
def p1_json():
    """Fixture for loading the p1.json file."""
    with open("testcases/p1.json", "r") as fr:
        return json.load(fr)
