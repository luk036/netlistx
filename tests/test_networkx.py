import networkx as nx


def test_Graph():
    ugraph = nx.Graph()
    ugraph.add_nodes_from([0, 1, 2, 3])
    ugraph.add_edge(0, 1)
    ugraph.add_edge(0, 1)
    assert ugraph.number_of_edges() == 1


if __name__ == "__main__":
    test_Graph()
