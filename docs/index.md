# 🖇  netlistx

Netlist representations and graph algorithms for electronic design automation.

## Installation

````bash
pip install netlistx
````

Python 3.11 or newer is required. Optional GPU acceleration (Numba CUDA):

````bash
pip install netlistx[gpu]
````

## Quickstart

````python
import networkx as nx
from netlistx.cover import min_vertex_cover
from netlistx.netlist import create_inverter

netlist = create_inverter()
print(netlist.number_of_modules(), netlist.number_of_nets())

graph = nx.Graph([(0, 1), (1, 2), (2, 0)])
cover, cost = min_vertex_cover(graph, {0: 1, 1: 1, 2: 1})
print(cover, cost)
````

## Contents

```{toctree}
:maxdepth: 2

Overview <readme>
Contributions & Help <contributing>
License <license>
Authors <authors>
Changelog <changelog>
Module Reference <api/modules>
Examples <figures_demo>
```

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
