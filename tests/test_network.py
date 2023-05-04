import showcase.network as nw
import networkx
import numpy as np
import pytest


@pytest.fixture
def terrain() -> np.ndarray:
    """Example digital elevation model"""
    N = 5
    r = np.random.random((N, N))
    s = np.arange(5)
    return r + s


@pytest.fixture
def network(terrain):
    """Example network"""
    resolution = 10
    return nw.Network(terrain, resolution)


def test_get_neighbour_indices(network):
    x, y = 2, 3
    N = network
    assert np.array_equal(
        N._get_neighbour_indices(x, y),
        np.array([(1, 2), (2, 2), (3, 2), (1, 3), (3, 3), (1, 4), (2, 4), (3, 4)]),
    )


def test_inside(network):
    N = network
    nrow, ncol = N.shape
    assert N._inside(ncol - 1, nrow - 1) == True
    assert N._inside(ncol, nrow) == False
    assert N._inside(-1, 0) == False


def test_graph(network):
    N = network
    nrow, ncol = N.shape
    graph = N.graph
    # number of nodes must be equal to array dimensions
    assert len(graph) == nrow * ncol
    # maximum number of edges
    if nrow >= 3 and ncol >= 3:
        assert len(graph.edges) <= (nrow - 2) * (ncol - 2) * 8
    # index attributes are set correctly
    x_data = networkx.get_node_attributes(graph, "x")
    y_data = networkx.get_node_attributes(graph, "y")
    for node in graph:
        assert x_data[node] + y_data[node] * nrow == node


def test_distance(network):
    assert network._calc_distance(0, 0, 3, 4) == 5.0
