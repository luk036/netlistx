"""
Random hypergraph netlist
=========================

Visualization of a random hypergraph netlist created by
``create_random_hgraph()``.
"""
import matplotlib.pyplot as plt
import networkx as nx
from netlistx.netlist import create_random_hgraph

netlist = create_random_hgraph(N=8, M=6, eta=0.3)
G = netlist.ugraph
modules = netlist.modules
nets = netlist.nets

pos = nx.bipartite_layout(G, modules)
plt.figure(figsize=(9, 6))
nx.draw_networkx_nodes(G, pos, nodelist=modules, node_color="coral",
                       node_shape="o", node_size=500, label="modules")
nx.draw_networkx_nodes(G, pos, nodelist=nets, node_color="cornflowerblue",
                       node_shape="s", node_size=400, label="nets")
nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)
nx.draw_networkx_labels(G, pos, font_size=9)
plt.title("Random hypergraph (N=8, M=6, η=0.3)")
plt.legend(framealpha=0.9)
plt.axis("off")
