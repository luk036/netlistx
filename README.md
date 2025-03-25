<!-- These are examples of badges you might want to add to your README:
     please update the URLs accordingly

[![Built Status](https://api.cirrus-ci.com/github/<USER>/netlistx.svg?branch=main)](https://cirrus-ci.com/github/<USER>/netlistx)
[![ReadTheDocs](https://readthedocs.org/projects/netlistx/badge/?version=latest)](https://netlistx.readthedocs.io/en/stable/)
[![Coveralls](https://img.shields.io/coveralls/github/<USER>/netlistx/main.svg)](https://coveralls.io/r/<USER>/netlistx)
[![PyPI-Server](https://img.shields.io/pypi/v/netlistx.svg)](https://pypi.org/project/netlistx/)
[![Conda-Forge](https://img.shields.io/conda/vn/conda-forge/netlistx.svg)](https://anaconda.org/conda-forge/netlistx)
[![Monthly Downloads](https://pepy.tech/badge/netlistx/month)](https://pepy.tech/project/netlistx)
[![Twitter](https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter)](https://twitter.com/netlistx)
-->

[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)
[![Documentation Status](https://readthedocs.org/projects/netlistx/badge/?version=latest)](https://netlistx.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/luk036/netlistx/branch/master/graph/badge.svg?token=6lpjUzPavX)](https://codecov.io/gh/luk036/netlistx)

# 🥅 netlistx

> Netlist and its related Algorithms in Python

This library defines a set of classes and functions for working with netlists, which are representations of electronic circuits. The main purpose of this library is to provide tools for creating, manipulating, and analyzing netlists.

The library doesn't take any direct inputs or produce any outputs on its own. Instead, it defines classes and functions that can be used by other parts of a program to work with netlists.

The main class in this library is the Netlist class. It represents a netlist as a graph, where modules (like electronic components) are connected by nets (like wires). The Netlist class takes three inputs when created: a graph representing the connections, a list of modules, and a list of nets.

The Netlist class provides several methods to get information about the netlist, such as the number of modules, nets, nodes, and pins. It also allows you to get the weight of modules and nets, which could represent things like the size or importance of components in the circuit.

The library includes several helper functions to create specific types of netlists. For example, create_inverter() creates a netlist representing a simple inverter circuit, while create_random_hgraph() creates a random netlist with a specified number of modules and nets.

The library uses graph theory concepts to represent the netlist. It uses the NetworkX library to handle the graph operations. The graph is represented as nodes (modules and nets) connected by edges (connections between modules and nets).

One important aspect of the library is how it handles the weights of modules and nets. It uses a RepeatArray class (which is not defined in this file) to efficiently store weights when many components have the same weight.

This library also implements several algorithms for solving different types of graph problems in graphs. The main purpose is to find minimal sets of vertices or edges that "cover" certain structures in a graph, such as all edges, cycles, or odd cycles.

The library takes various inputs depending on the specific function being used. Generally, it requires a graph structure (either a regular graph or a hypergraph), a weight mapping for the vertices, and sometimes an optional initial set. The graphs are typically represented using the NetworkX library (nx.Graph).

The outputs produced by these functions are usually a tuple containing two elements: a set representing the minimal cover found, and a number representing the total weight or cost of that cover.

The library achieves its purpose through several different algorithms, but they all follow a similar pattern called the primal-dual approximation method. This method iteratively builds a solution by selecting elements that violate certain conditions and adding them to the cover set.

The library uses several important data structures and algorithms. Graphs are represented using NetworkX, which provides efficient graph operations. The algorithms make heavy use of sets for storing covers and dictionaries for storing weights and other information. The cycle-finding algorithms use breadth-first search and clever bookkeeping to efficiently detect cycles in the graph.

The library also includes functions for reading netlists from JSON files and for creating specific test netlists. These functions could be useful for testing or demonstrating the capabilities of the Netlist class.

Overall, this library provides a foundation for working with netlists in Python. It allows programmers to create, manipulate, and analyze netlists, which could be useful in electronic design automation tools or circuit analysis software.

## Depend on

- [mywheel](https://github.com/luk036/mywheel)
- networkx

## 👀 See also

- [netlistx-cpp](https://github.com/luk036/netlistx-cpp)
- [slides](https://luk036.github.io/algo4dfm/primal_dual.html)

## Used by

- [ckpttnpy](https://github.com/luk036/ckpttnpy)

## 👉 Note

This project has been set up using PyScaffold 4.5. For details and usage
information on PyScaffold see https://pyscaffold.org/.
