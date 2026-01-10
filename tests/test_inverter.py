from typing import Any

import pytest

from netlistx.netlist import create_inverter, create_inverter2


@pytest.mark.parametrize(
    "create_fn, weight_type",
    [(create_inverter, dict), (create_inverter2, list)],
)
def test_inverter(create_fn: Any, weight_type: Any) -> None:
    hyprgraph = create_fn()
    assert hyprgraph.number_of_modules() == 3
    assert hyprgraph.number_of_nets() == 2
    assert hyprgraph.number_of_nodes() == 5
    assert hyprgraph.number_of_pins() == 4
    assert hyprgraph.get_max_degree() == 2
    assert isinstance(hyprgraph.module_weight, weight_type)
