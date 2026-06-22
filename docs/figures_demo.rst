Figures Demo
============

This page demonstrates the ``.. plot::`` directive from
``matplotlib.sphinxext.plot_directive`` for generating figures
directly from Python code in Sphinx documentation.

Referencing an external script
------------------------------

.. plot:: examples/plot_netlist_graph.py

.. plot:: examples/plot_random_hgraph.py

The plot inline directive
-------------------------

You can also embed the plotting code directly in the RST file.
Here is a simple star graph drawn with networkx:

.. plot::

   import matplotlib.pyplot as plt
   import networkx as nx

   G = nx.star_graph(8)
   pos = nx.spring_layout(G, seed=42)
   plt.figure(figsize=(6, 5))
   nx.draw_networkx(G, pos, node_color="plum", node_size=400, with_labels=True)
   plt.title("Star graph with 8 leaves")
   plt.axis("off")

Controlling options
-------------------

Use ``:width:``, ``:alt:``, and ``:align:`` as with any figure:

.. plot:: examples/plot_netlist_graph.py
   :width: 60%
   :align: center
   :alt: Netlist bipartite graph at 60% width
