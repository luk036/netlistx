"""
Netlist.py

This code defines a set of classes and functions for working with netlists, which are representations of electronic circuits. The main purpose of this code is to provide tools for creating, manipulating, and analyzing netlists.

The code doesn't take any direct inputs or produce any outputs on its own. Instead, it defines classes and functions that can be used by other parts of a program to work with netlists.

The main class in this code is the Netlist class. It represents a netlist as a graph, where modules (like electronic components) are connected by nets (like wires). The Netlist class takes three inputs when created: a graph representing the connections, a list of modules, and a list of nets.

The Netlist class provides several methods to get information about the netlist, such as the number of modules, nets, nodes, and pins. It also allows you to get the weight of modules and nets, which could represent things like the size or importance of components in the circuit.

The code includes several helper functions to create specific types of netlists. For example, create_inverter() creates a netlist representing a simple inverter circuit, while create_random_hgraph() creates a random netlist with a specified number of modules and nets.

The code uses graph theory concepts to represent the netlist. It uses the NetworkX library to handle the graph operations. The graph is represented as nodes (modules and nets) connected by edges (connections between modules and nets).

One important aspect of the code is how it handles the weights of modules and nets. It uses a RepeatArray class (which is not defined in this file) to efficiently store weights when many components have the same weight.

The code also includes functions for reading netlists from JSON files and for creating specific test netlists. These functions could be useful for testing or demonstrating the capabilities of the Netlist class.

Overall, this code provides a foundation for working with netlists in Python. It allows programmers to create, manipulate, and analyze netlists, which could be useful in electronic design automation tools or circuit analysis software.
"""

import json
import random
from typing import Any, List, Union

import networkx as nx
from mywheel.array_like import RepeatArray
from mywheel.map_adapter import MapAdapter
from networkx.algorithms import bipartite
from networkx.readwrite import json_graph


# The class SimpleGraph is a subclass of nx.Graph and defines default attributes for edges and nodes.
class SimpleGraph(nx.Graph):
    all_edge_dict = {"weight": 1}

    def single_edge_dict(self):
        return self.all_edge_dict

    edge_attr_dict_factory = single_edge_dict
    node_attr_dict_factory = single_edge_dict


# The TinyGraph class is a subclass of nx.Graph that initializes a graph with a specified number of
# nodes and provides methods for creating node dictionaries and adjacency list dictionaries.
class TinyGraph(nx.Graph):
    num_nodes = 0

    def cheat_node_dict(self):
        return MapAdapter([dict() for _ in range(self.num_nodes)])

    def cheat_adjlist_outer_dict(self):
        return MapAdapter([dict() for _ in range(self.num_nodes)])

    node_dict_factory = cheat_node_dict
    adjlist_outer_dict_factory = cheat_adjlist_outer_dict

    def init_nodes(self, n: int):
        self.num_nodes = n
        self._node = self.cheat_node_dict()
        self._adj = self.cheat_adjlist_outer_dict()
        # self._pred = self.cheat_adjlist_outer_dict()


# The `Netlist` class represents a netlist, which is a collection of modules and nets in a graph
# structure, and provides various properties and methods for working with the netlist.
class Netlist:
    num_pads = 0
    cost_model = 0

    def __init__(
        self,
        ugraph: nx.Graph,
        modules: Union[range, List[Any]],
        nets: Union[range, List[Any]],
    ):
        """
        The function initializes an object with a graph, modules, and nets, and calculates some properties
        of the graph.

        :param ugraph: The parameter `ugraph` is a graph object of type `nx.Graph`. It represents the graph
            structure of the system
        :type ugraph: nx.Graph
        :param modules: The `modules` parameter is a list or range object that represents the modules in the
            graph. Each module is a node in the graph
        :type modules: Union[range, List[Any]]
        :param nets: The `nets` parameter is a list or range that represents the nets in the graph. A net is
            a connection between two or more modules
        :type nets: Union[range, List[Any]]
        """
        self.ugraph = ugraph
        self.modules = modules
        self.nets = nets

        self.num_modules = len(modules)
        self.num_nets = len(nets)
        # self.net_weight: Optional[Union[Dict, List[int]]] = None
        self.module_weight = RepeatArray(1, self.num_modules)
        self.module_fixed: set = set()

        # self.module_dict = {}
        # for v in enumerate(self.module_list):
        #     self.module_dict[v] = v

        # self.net_dict = {}
        # for i_net, net in enumerate(self.net_list):
        #     self.net_dict[net] = i_net

        # self.module_fixed = module_fixed
        # self.has_fixed_modules = (self.module_fixed != [])
        self.max_degree = max(self.ugraph.degree[cell] for cell in modules)
        # self.max_net_degree = max(self.ugraph.degree[net] for net in nets)

    def number_of_modules(self) -> int:
        """
        The function "number_of_modules" returns the number of modules.
        :return: The method is returning the value of the attribute `num_modules`.
        """
        return self.num_modules

    def number_of_nets(self) -> int:
        """
        The function "number_of_nets" returns the number of nets.
        :return: The number of nets.
        """
        return self.num_nets

    def number_of_nodes(self) -> int:
        """
        The function "number_of_nodes" returns the number of nodes in a graph.
        :return: The number of nodes in the graph.
        """
        return self.ugraph.number_of_nodes()

    def number_of_pins(self) -> int:
        """
        The function `number_of_pins` returns the number of edges in a graph.
        :return: The number of edges in the graph.
        """
        return self.ugraph.number_of_edges()

    def get_max_degree(self) -> int:
        """
        The function `get_max_degree` returns the maximum degree of nodes in a graph.
        :return: the maximum degree of the nodes in the graph.
        """
        return max(self.ugraph.degree[cell] for cell in self.modules)

    def get_module_weight(self, v) -> int:
        """
        The function `get_module_weight` returns the weight of a module given its index.

        :param v: The parameter `v` in the `get_module_weight` function is of type `size_t`. It represents
            the index or key of the module weight that you want to retrieve
        :return: the value of `self.module_weight[v]`.
        """
        return self.module_weight[v]

    # def get_module_weight_by_id(self, v):
    #     """[summary]

    #     Arguments:
    #         v (size_t):  description

    #     Returns:
    #         [size_t]:  description
    #     """
    #     return 1 if self.module_weight is None \
    #         else self.module_weight[v]

    def get_net_weight(self, _) -> int:
        """
        The function `get_net_weight` returns an integer value.

        :param _: The underscore (_) in the function signature is a convention in Python to indicate that
            the parameter is not used within the function. It is often used when a parameter is required by the
            function signature but not actually used within the function's implementation. In this case, the
            underscore (_) is used as a placeholder for
        :return: An integer value of 1 is being returned.
        """
        return 1

    def __iter__(self):
        """
        The function returns an iterator over all modules in the Netlist.
        :return: The `iter(self.modules)` is being returned.
        """
        return iter(self.modules)


def read_json(filename):
    """
    The function `read_json` reads a JSON file, converts it into a graph, and creates a netlist object
    with module and net weights.

    :param filename: The filename parameter is the name of the JSON file that contains the data you want
        to read
    :return: an object of type `Netlist`.
    """
    with open(filename, "r") as fr:
        data = json.load(fr)
    ugraph = json_graph.node_link_graph(data)
    num_modules = ugraph.graph["num_modules"]
    num_nets = ugraph.graph["num_nets"]
    num_pads = ugraph.graph["num_pads"]
    hyprgraph = Netlist(
        ugraph, range(num_modules), range(num_modules, num_modules + num_nets)
    )
    hyprgraph.num_pads = num_pads
    # hyprgraph.module_weight = RepeatArray(1, num_modules)
    # hyprgraph.net_weight = ShiftArray(1 for _ in range(num_nets))
    # hyprgraph.net_weight.set_start(num_modules)
    return hyprgraph


def create_inverter():
    gr = SimpleGraph()
    gr.add_nodes_from(["a0", "p1", "p2", "n0", "n1"])
    nets = ["n0", "n1"]
    modules = ["a0", "p1", "p2"]
    module_weight = {"a0": 1, "p1": 0, "p2": 0}

    gr.add_edges_from(
        [
            ("n0", "p1", {"dir": "I"}),
            ("n0", "a0", {"dir": "O"}),
            ("n1", "a0", {"dir": "I"}),
            ("n1", "p2", {"dir": "O"}),
        ]
    )
    gr.graph["num_modules"] = 3
    gr.graph["num_nets"] = 2
    gr.graph["num_pads"] = 2
    hyprgraph = Netlist(gr, modules, nets)
    hyprgraph.module_weight = module_weight
    hyprgraph.net_weight = RepeatArray(1, len(nets))
    hyprgraph.num_pads = 2
    return hyprgraph


def create_inverter2():
    gr = SimpleGraph()
    gr.add_nodes_from([0, 1, 2, 3, 4])
    nets = range(3, 5)
    modules = range(3)
    module_weight = [1, 0, 0]

    gr.add_edges_from(
        [
            (3, 1, {"dir": "I"}),
            (3, 0, {"dir": "O"}),
            (4, 0, {"dir": "I"}),
            (4, 2, {"dir": "O"}),
        ]
    )
    gr.graph["num_modules"] = 3
    gr.graph["num_nets"] = 2
    gr.graph["num_pads"] = 2
    hyprgraph = Netlist(gr, modules, nets)
    hyprgraph.module_weight = module_weight
    hyprgraph.net_weight = RepeatArray(1, len(nets))
    hyprgraph.num_pads = 2
    return hyprgraph


def create_drawf():
    """
    The function `create_drawf` creates a graph and netlist object with specified nodes, edges, and
    weights.
    :return: an instance of the Netlist class, which is created using the SimpleGraph class and some
        predefined modules and nets.
    """
    ugraph = SimpleGraph()
    ugraph.add_nodes_from(
        [
            "a0",
            "a1",
            "a2",
            "a3",
            "p1",
            "p2",
            "p3",
            "n0",
            "n1",
            "n2",
            "n3",
            "n4",
            "n5",
        ]
    )
    nets = [
        "n0",
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
    ]
    # net_map = {net: i_net for i_net, net in enumerate(nets)}
    modules = ["a0", "a1", "a2", "a3", "p1", "p2", "p3"]
    # module_map = {v: i_v for i_v, v in enumerate(modules)}
    # module_weight = [1, 3, 4, 2, 0, 0, 0]
    module_weight = {"a0": 1, "a1": 3, "a2": 4, "a3": 2, "p1": 0, "p2": 0, "p3": 0}

    ugraph.add_edges_from(
        [
            ("n0", "p1", {"dir": "I"}),
            ("n0", "a0", {"dir": "I"}),
            ("n0", "a1", {"dir": "O"}),
            ("n1", "a0", {"dir": "I"}),
            ("n1", "a2", {"dir": "I"}),
            ("n1", "a3", {"dir": "O"}),
            ("n2", "a1", {"dir": "I"}),
            ("n2", "a2", {"dir": "I"}),
            ("n2", "a3", {"dir": "O"}),
            ("n3", "a2", {"dir": "I"}),
            ("n3", "p2", {"dir": "O"}),
            ("n4", "a3", {"dir": "I"}),
            ("n4", "p3", {"dir": "O"}),
            ("n5", "p2", {"dir": "B"}),
        ]
    )
    ugraph.graph["num_modules"] = 7
    ugraph.graph["num_nets"] = 6
    ugraph.graph["num_pads"] = 3
    hyprgraph = Netlist(ugraph, modules, nets)
    hyprgraph.module_weight = module_weight
    hyprgraph.net_weight = RepeatArray(1, len(nets))
    hyprgraph.num_pads = 3
    return hyprgraph


def create_test_netlist():
    """
    The function `create_test_netlist` creates a test netlist with nodes, edges, module weights, and net
    weights.
    :return: an instance of the `Netlist` class, which represents a netlist with modules and nets.
    """
    ugraph = SimpleGraph()
    ugraph.add_nodes_from(["a0", "a1", "a2", "a3", "a4", "a5"])
    # module_weight = [533, 543, 532]
    module_weight = {"a0": 533, "a1": 543, "a2": 532}
    ugraph.add_edges_from(
        [
            ("a3", "a0"),
            ("a3", "a1"),
            ("a4", "a0"),
            ("a4", "a1"),
            ("a4", "a2"),
            ("a5", "a0"),  # self-loop
        ]
    )

    ugraph.graph["num_modules"] = 3
    ugraph.graph["num_nets"] = 3
    modules = ["a0", "a1", "a2"]
    # module_map = {v: i_v for i_v, v in enumerate(modules)}
    nets = ["a3", "a4", "a5"]
    # net_weight = {net: 1 for net in nets}
    net_weight = RepeatArray(1, len(nets))

    hyprgraph = Netlist(ugraph, modules, nets)
    hyprgraph.module_weight = module_weight
    hyprgraph.net_weight = net_weight
    return hyprgraph


def vdc(n, base=2):
    """[summary]

    Arguments:
        n ([type]): [description]

    Keyword Arguments:
        base (int): [description] (default: {2})

    Returns:
        [type]: [description]
    """
    vdc, denom = 0.0, 1.0
    while n:
        denom *= base
        n, remainder = divmod(n, base)
        vdc += remainder / denom
    return vdc


def vdcorput(n, base=2):
    """[summary]

    Arguments:
        n (int): number of vectors

    Keyword Arguments:
        base (int): [description] (default: {2})

    Returns:
        [type]: [description]
    """
    return [vdc(i, base) for i in range(n)]


def form_graph(N, M, _, eta, seed=None):  # ignore pos
    """Form N by N grid of nodes, connect nodes within eta.
        mu and eta are relative to 1/(N-1)

    Arguments:
        t (float): the best-so-far optimal value
        pos ([type]): [description]
        eta ([type]): [description]

    Keyword Arguments:
        seed ([type]): [description] (default: {None})

    Returns:
        [type]: [description]
    """
    if seed:
        random.seed(seed)

    # connect nodes with edges
    ugraph = bipartite.random_graph(N, M, eta)
    # ugraph = nx.DiGraph(ugraph)
    return ugraph


def create_random_hgraph(N=30, M=26, eta=0.1):
    T = N + M
    xbase = 2
    ybase = 3
    x = [i for i in vdcorput(T, xbase)]
    y = [i for i in vdcorput(T, ybase)]
    pos = zip(x, y)
    ugraph = form_graph(N, M, pos, eta, seed=5)

    ugraph.graph["num_modules"] = N
    ugraph.graph["num_nets"] = M
    hyprgraph = Netlist(ugraph, range(N), range(N, N + M))
    hyprgraph.module_weight = RepeatArray(1, N)
    hyprgraph.net_weight = RepeatArray(1, M)
    # hyprgraph.net_weight = ShiftArray(1 for _ in range(M))
    # hyprgraph.net_weight.set_start(N)
    return hyprgraph
