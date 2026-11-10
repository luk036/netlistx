from importlib.metadata import PackageNotFoundError, version

from netlistx.cover import min_cycle_cover, min_hyper_vertex_cover, min_odd_cycle_cover, min_vertex_cover, pd_cover
from netlistx.graph_algo import min_maximal_independent_set, min_vertex_cover_fast
from netlistx.hadlock import solve_hadlock_max_cut, validate_max_cut
from netlistx.netlist import Netlist, SimpleGraph, TinyGraph, create_drawf, create_inverter, create_inverter2, create_random_hgraph, create_test_netlist
from netlistx.netlist_algo import min_maximal_matching
from netlistx.rand_cover import rand_hyper_vertex_cover, rand_vertex_cover
from netlistx.readwrite import read_are, read_json, read_netd, read_yosys_json, read_yosys_json_directed, read_yosys_json_sax
from netlistx.tsp import calculate_total_distance, christofides_tsp, make_l1_graph, make_l2_graph, solve_christofides_2opt_tsp, two_opt

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

__all__ = [
    "__version__",
    "Netlist",
    "SimpleGraph",
    "TinyGraph",
    "create_drawf",
    "create_inverter",
    "create_inverter2",
    "create_random_hgraph",
    "create_test_netlist",
    "pd_cover",
    "min_vertex_cover",
    "min_hyper_vertex_cover",
    "min_cycle_cover",
    "min_odd_cycle_cover",
    "min_vertex_cover_fast",
    "min_maximal_independent_set",
    "min_maximal_matching",
    "rand_vertex_cover",
    "rand_hyper_vertex_cover",
    "solve_hadlock_max_cut",
    "validate_max_cut",
    "read_are",
    "read_json",
    "read_netd",
    "read_yosys_json",
    "read_yosys_json_directed",
    "read_yosys_json_sax",
    "calculate_total_distance",
    "christofides_tsp",
    "make_l1_graph",
    "make_l2_graph",
    "solve_christofides_2opt_tsp",
    "two_opt",
]
