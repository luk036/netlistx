import networkx as nx


def test_Graph():
    gra = nx.Graph()
    gra.add_nodes_from([0, 1, 2, 3])
    gra.add_edge(0, 1)
    gra.add_edge(0, 1)
    assert gra.number_of_edges() == 1


if __name__ == "__main__":
    test_Graph()
