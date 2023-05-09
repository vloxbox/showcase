import networkx as nx
import numpy as np
import pytest
from showcase.graph import Graph
from showcase.parameters import ELEV


@pytest.fixture
def graph() -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_node(1, x=1, y=1, release=1)
    g.add_node(0, x=1, y=0, release=0)
    g.add_node(2, x=0, y=2, release=0)
    g.add_node(3, x=2, y=2, release=0)
    g.add_node(4, x=1, y=3, release=0)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(1, 3)
    g.add_edge(3, 4)
    return g


@pytest.fixture
def data() -> np.ndarray:
    return np.ones((2, 2))


@pytest.fixture
def dem() -> np.ndarray:
    return np.array([[1.0, 2.0], [0.0, 1.5]])


def test_from_dem(dem):
    g = Graph.from_dem(dem)
    assert g.nodes[1][ELEV] == 2.0
    assert set(list(g.nodes)) == set([0, 1, 2, 3])
    assert set(Graph.get_children(g, 1)) == set([0, 2, 3])
    assert set(Graph.get_children(g, 0)) == set(
        [
            2,
        ]
    )
    assert set(Graph.get_children(g, 3)) == set([0, 2])
    assert set(list(g.edges)) == set([(1, 0), (1, 2), (1, 3), (3, 0), (3, 2), (0, 2)])


def test_find_all_successors(graph):
    assert set(Graph.find_all_successors(graph, 1)) == set([1, 2, 3, 4])
    assert Graph.find_all_successors(graph, 4) == [
        4,
    ]


def test_find_all_start_nodes(graph):
    assert Graph.find_all_start_nodes(graph) == [0]


def test_is_start_node(graph):
    assert Graph.is_start_node(graph, 0)
    assert not Graph.is_start_node(graph, 1)


def test_sort_graph(graph):
    assert set(Graph.sort_graph(graph)) == set([0, 1, 2, 3, 4])


def test_get_children(graph):
    assert set(Graph.get_children(graph, 1)) == set([2, 3])
    assert Graph.get_children(graph, 4) == []


def test_get_parents(graph):
    assert Graph.get_parents(graph, 4) == [3]


def test_get_coordinates(graph):
    x, y = Graph.get_coordinates(graph, 0)
    assert (x, y) == (1, 0)


def test_add_data_from_array(graph, data):
    field = "test"
    g = graph
    Graph.add_data_from_array(g, data, field)
    for i in g:
        if i < 4:
            assert g.nodes[i][field] == 1
        else:
            assert field not in g.nodes[i]


def test_to_array():
    assert True
