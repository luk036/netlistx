"""Tests for readwrite module (IBM .net/.are format reader).

Ported from netlistx-cpp/test/source/test_readwrite.cpp.
"""
from netlistx.readwrite import read_are, read_netd


def test_read_ibm01() -> None:
    hyprgraph = read_netd("testcases/ibm01.net")

    assert hyprgraph.number_of_modules() == 12752
    assert hyprgraph.number_of_nets() == 14111
    assert hyprgraph.get_max_degree() == 39
    assert hyprgraph.get_module_weight(1) == 1
    assert hyprgraph.num_pads == 246


def test_read_ibm01_with_are() -> None:
    hyprgraph = read_netd("testcases/ibm01.net")
    read_are(hyprgraph, "testcases/ibm01.are")

    assert hyprgraph.number_of_modules() == 12752
    assert hyprgraph.get_max_degree() == 39
    assert hyprgraph.get_module_weight(0) == 256
    assert hyprgraph.get_module_weight(1) == 224
    # Pad nodes (at the end) should have weight 0
    pad_idx = hyprgraph.num_modules - 1
    assert hyprgraph.get_module_weight(pad_idx) == 0
