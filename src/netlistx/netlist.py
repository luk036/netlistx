# -*- coding: utf-8 -*-

import json
import random
from typing import Dict, List, Set, Optional, Union

import networkx as nx
from networkx.algorithms import bipartite
from networkx.readwrite import json_graph


# The `ThinGraph` class is a subclass of `nx.Graph` that defines default attributes for edges and
# nodes.
class ThinGraph(nx.Graph):
    all_edge_dict = {"weight": 1}

    def single_edge_dict(self):
        return self.all_edge_dict

    edge_attr_dict_factory = single_edge_dict
    node_attr_dict_factory = single_edge_dict


# The class SimpleGraph is a subclass of nx.Graph and defines default attributes for edges and nodes.
class SimpleGraph(nx.Graph):
    all_edge_dict = {"weight": 1}

    def single_edge_dict(self):
        return self.all_edge_dict

    edge_attr_dict_factory = single_edge_dict
    node_attr_dict_factory = single_edge_dict


class Netlist:
    num_pads = 0
    cost_model = 0

    def __init__(
        self, gra: nx.Graph, modules: Union[range, List], nets: Union[range, List]
    ):
        """
        The function initializes an object with a graph, modules, and nets, and calculates various
        properties of the graph and modules.

        :param gra: The parameter `gra` is a graph object representing the connectivity between modules and
        nets. It is an instance of the `nx.Graph` class from the NetworkX library
        :type gra: nx.Graph
        :param modules: The `modules` parameter represents a collection of nodes in a graph. It can be
        either a range or a list of nodes
        :type modules: Union[range, List]
        :param nets: The `nets` parameter represents a collection of nets in a graph. A net is a connection
        between two or more modules in a circuit or network. It can be represented as a range or a list of
        net identifiers
        :type nets: Union[range, List]
        """
        self.gra = gra
        self.modules = modules
        self.nets = nets

        self.num_modules = len(modules)
        self.num_nets = len(nets)
        self.net_weight: Optional[Union[Dict, List[int]]] = None
        self.module_weight: Optional[Union[Dict, List[int]]] = None
        self.module_fixed: Set = set()

        self.max_degree = max(self.gra.degree[cell] for cell in modules)
        self.max_net_degree = max(self.gra.degree[net] for net in nets)

    def number_of_modules(self) -> int:
        """
        The function "number_of_modules" returns the number of modules.
        :return: The method is returning the value of the attribute `num_modules`.
        """
        return self.num_modules

    def number_of_nets(self) -> int:
        """[summary]

        Returns:
            dtype:  description
        """
        return self.num_nets

    def number_of_nodes(self) -> int:
        """[summary]

        Returns:
            dtype:  description
        """
        return self.gra.number_of_nodes()

    def number_of_pins(self) -> int:
        """[summary]

        Returns:
            dtype:  description
        """
        return self.gra.number_of_edges()

    def get_max_degree(self) -> int:
        """[summary]

        Returns:
            dtype:  description
        """
        return self.max_degree

    def get_max_net_degree(self) -> int:
        """[summary]

        Returns:
            dtype:  description
        """
        return self.max_net_degree

    def get_module_weight(self, vtx) -> int:
        """[summary]

        Arguments:
            vtx (size_t):  description

        Returns:
            [size_t]:  description
        """
        return 1 if self.module_weight is None else self.module_weight[vtx]

    # def get_module_weight_by_id(self, vtx):
    #     """[summary]

    #     Arguments:
    #         vtx (size_t):  description

    #     Returns:
    #         [size_t]:  description
    #     """
    #     return 1 if self.module_weight is None \
    #         else self.module_weight[vtx]

    def get_net_weight(self, _) -> int:
        """[summary]

        Arguments:
            i_net (size_t):  description

        Returns:
            size_t:  description
        """
        return 1


def read_json(filename):
    with open(filename, "r") as fr:
        data = json.load(fr)
    gra = json_graph.node_link_graph(data)
    num_modules = gra.graph["num_modules"]
    num_nets = gra.graph["num_nets"]
    num_pads = gra.graph["num_pads"]
    hyprgraph = Netlist(
        gra, range(num_modules), range(num_modules, num_modules + num_nets)
    )
    hyprgraph.num_pads = num_pads
    return hyprgraph


def create_drawf():
    gra = ThinGraph()
    gra.add_nodes_from(
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
    modules = ["a0", "a1", "a2", "a3", "p1", "p2", "p3"]
    module_weight = {"a0": 1, "a1": 3, "a2": 4, "a3": 2, "p1": 0, "p2": 0, "p3": 0}

    gra.add_edges_from(
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
    gra.graph["num_modules"] = 7
    gra.graph["num_nets"] = 6
    gra.graph["num_pads"] = 3
    hyprgraph = Netlist(gra, modules, nets)
    hyprgraph.module_weight = module_weight
    hyprgraph.num_pads = 3
    return hyprgraph


def create_test_netlist():
    gra = ThinGraph()
    gra.add_nodes_from(["a0", "a1", "a2", "a3", "a4", "a5"])
    module_weight = {"a0": 533, "a1": 543, "a2": 532}
    gra.add_edges_from(
        [
            ("a3", "a0"),
            ("a3", "a1"),
            ("a4", "a0"),
            ("a4", "a1"),
            ("a4", "a2"),
            ("a5", "a0"),  # self-loop
        ]
    )

    gra.graph["num_modules"] = 3
    gra.graph["num_nets"] = 3
    modules = ["a0", "a1", "a2"]
    nets = ["a3", "a4", "a5"]

    hyprgraph = Netlist(gra, modules, nets)
    hyprgraph.module_weight = module_weight
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


def form_graph(ndim, mdim, _, eta, seed=None):
    """Form N by N grid of nodes, connect nodes within eta.
        mu and eta are relative to 1/(N-1)

    Arguments:
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
    gra = bipartite.random_graph(ndim, mdim, eta)
    return gra


def create_random_graph(N=30, M=26, eta=0.1):
    T = N + M
    xbase = 2
    ybase = 3
    x = [i for i in vdcorput(T, xbase)]
    y = [i for i in vdcorput(T, ybase)]
    pos = zip(x, y)
    gra = form_graph(N, M, pos, eta, seed=5)

    gra.graph["num_modules"] = N
    gra.graph["num_nets"] = M
    hyprgraph = Netlist(gra, range(N), range(N, N + M))
    return hyprgraph
