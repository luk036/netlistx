"""Readers for IBM-PLACE 2.0 benchmark format (.net + .are).

Port of netlistx-cpp/source/readwrite.cpp readNetD and readAre.
"""
from typing import List

import networkx as nx

from netlistx.netlist import Netlist


def read_netd(filename: str) -> Netlist:
    """Read an IBM .net format file and return a Netlist.

    Header format: 0 numPins numNets numModules padOffset

    Each entry line: a<id> s|l [netnum]  (cell) or p<id> s|l [netnum]  (pad)
    - 's' marks the start of a new net
    - 'l' continues the current net (connections to the most recent 's' net)
    """
    with open(filename, "r") as f:
        lines = f.readlines()

    numPins = int(lines[1].strip())
    numNets = int(lines[2].strip())
    numModules = int(lines[3].strip())
    padOffset = int(lines[4].strip())

    total_nodes = numModules + numNets
    graph = nx.Graph()
    graph.add_nodes_from(range(numModules), bipartite=0)
    graph.add_nodes_from(range(numModules, total_nodes), bipartite=1)

    edgeIdx = numModules - 1
    pin_count = 0
    for line in lines[5:]:
        if pin_count >= numPins:
            break
        line = line.strip()
        if not line:
            continue
        entry = line.split()[0]
        kind = entry[0]
        node = int(entry[1:])
        if kind == "p":
            node += padOffset
        if " s " in line or line.endswith(" s") or " s\t" in line:
            edgeIdx += 1
        graph.add_edge(node, edgeIdx)
        pin_count += 1

    modules = list(range(numModules))
    net_nodes = list(range(numModules, numModules + numNets))
    hyprgraph = Netlist(graph, modules, net_nodes)
    hyprgraph.num_pads = numModules - padOffset - 1

    return hyprgraph


def read_are(hyprgraph: Netlist, filename: str) -> None:
    """Read an IBM .are format file and update module_weight in-place.

    Format: a<id> <weight> or p<id> <weight>
    For pads (p), offset is computed from num_modules - num_pads - 1.
    """
    pad_offset = hyprgraph.num_modules - hyprgraph.num_pads - 1
    module_weight: List[int] = [1] * hyprgraph.num_modules

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            entry = parts[0]
            weight = int(parts[1])
            kind = entry[0]
            node = int(entry[1:])
            if kind == "p":
                node += pad_offset
            module_weight[node] = weight

    hyprgraph.module_weight = module_weight
