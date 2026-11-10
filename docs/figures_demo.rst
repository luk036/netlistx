Examples
========

Bipartite netlist graph
-----------------------

The ``.. plot::`` directive from ``matplotlib.sphinxext.plot_directive``
renders a script in ``docs/examples/`` directly into the page.

.. plot:: examples/plot_netlist_graph.py

Random hypergraph
-----------------

.. plot:: examples/plot_random_hgraph.py

Figure options
--------------

Use ``:width:``, ``:alt:``, and ``:align:`` as with any figure:

.. plot:: examples/plot_netlist_graph.py
   :width: 60%
   :align: center
   :alt: Netlist bipartite graph at 60% width

Yosys and Liberty tutorials
---------------------------

The scripts in ``examples/yosys/`` demonstrate Liberty parsing, JSON
conversion, timing extraction, and Yosys-to-Liberty conversion. Run them
from any directory; they resolve their data files relative to the script:

.. code-block:: bash

   python examples/yosys/tutorial_parse_lib.py
   python examples/yosys/tutorial_convert_json.py
   python examples/yosys/tutorial_extract_timing.py
   python examples/yosys/yosys_to_liberty.py

Install their extra dependencies with ``pip install netlistx[examples]``.
