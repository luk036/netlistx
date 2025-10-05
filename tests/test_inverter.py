from netlistx.netlist import create_inverter, create_inverter2


def test_inverter():
    hyprgraph = create_inverter()
    assert hyprgraph.number_of_modules() == 3
    assert hyprgraph.number_of_nets() == 2
    assert hyprgraph.number_of_nodes() == 5
    assert hyprgraph.number_of_pins() == 4
    assert hyprgraph.get_max_degree() == 2
    assert isinstance(hyprgraph.module_weight, dict)


def test_inverter2():
    hyprgraph = create_inverter2()
    assert hyprgraph.number_of_modules() == 3
    assert hyprgraph.number_of_nets() == 2
    assert hyprgraph.number_of_nodes() == 5
    assert hyprgraph.number_of_pins() == 4
    assert hyprgraph.get_max_degree() == 2
    assert isinstance(hyprgraph.module_weight, list)
