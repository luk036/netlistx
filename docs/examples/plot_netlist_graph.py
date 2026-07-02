"""
Netlist bipartite graph
=======================

Bipartite visualization of an inverter netlist with modules (circles)
and nets (squares) using the Netlist class.
"""
import matplotlib.pyplot as plt
import networkx as nx

from netlistx.netlist import create_inverter

netlist = create_inverter()
G = netlist.ugraph  # bipartite graph
modules = netlist.modules
nets = netlist.nets

pos = nx.bipartite_layout(G, modules)
plt.figure(figsize=(8, 5))
nx.draw_networkx_nodes(
    G,
    pos,
    nodelist=modules,
    node_color="lightblue",
    node_shape="o",
    node_size=600,
    label="modules",
)
nx.draw_networkx_nodes(
    G,
    pos,
    nodelist=nets,
    node_color="lightgreen",
    node_shape="s",
    node_size=500,
    label="nets",
)
nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.6)
nx.draw_networkx_labels(G, pos, font_size=10)
plt.title("Inverter netlist — bipartite graph")
plt.legend(framealpha=0.9)
plt.axis("off")
