from typing import Any

import pytest
import json
from netlistx.netlist import create_drawf, read_json


@pytest.fixture
def drawf_graph() -> Any:
    """Fixture for creating a hypergraph from the drawf file."""
    return create_drawf()


@pytest.fixture
def p1_graph() -> Any:
    """Fixture for creating a hypergraph from the p1.json file."""
    return read_json("testcases/p1.json")


@pytest.fixture
def drawf_json() -> Any:
    """Fixture for loading the drawf.json file."""
    with open("testcases/drawf.json", "r") as fr:
        data = json.load(fr)
    
    # Convert 'links' to 'edges' for NetworkX compatibility
    if 'links' in data and 'edges' not in data:
        data['edges'] = data.pop('links')
    
    return data


@pytest.fixture
def p1_json() -> Any:
    """Fixture for loading the p1.json file."""
    with open("testcases/p1.json", "r") as fr:
        data = json.load(fr)
    
    # Convert 'links' to 'edges' for NetworkX compatibility
    if 'links' in data and 'edges' not in data:
        data['edges'] = data.pop('links')
    
    return data
