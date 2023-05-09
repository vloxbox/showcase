import numpy as np
import networkx as nx
import pytest
import showcase.flow as flow
from showcase.parameters import X, Y, ELEV, DIST, ZD, PERS, FLUX, REL


N = 10
RES = 1
ALPHA = 10
ZD_MAX = 1000
EXP = 4


@pytest.fixture
def terrain() -> np.ndarray:
    """Example digital elevation model"""
    range = np.arange(N)
    return range * np.ones((N, N))


@pytest.fixture
def release() -> np.ndarray:
    """Release array"""
    array = np.zeros((N, N))
    array[N - 1, int(N / 2)] = 1
    array[N - 2, int(N / 2)] = 2
    return array


@pytest.fixture
def f(terrain) -> flow.Flow:
    return flow.Flow(
        graph=terrain,
        resolution=RES,
        alpha=ALPHA,
        z_delta_max=ZD_MAX,
        exponent=EXP,
    )


@pytest.fixture
def graph() -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_node(0, **{X: 1, Y: 0, ELEV: 5.0})
    g.add_node(1, **{X: 1, Y: 1, ELEV: 4.0})
    g.add_node(2, **{X: 0, Y: 2, ELEV: 1.0})
    g.add_node(3, **{X: 2, Y: 2, ELEV: 3.0})
    g.add_node(4, **{X: 1, Y: 3, ELEV: 1.0})
    g.add_edge(0, 1, **{DIST: 1.0})
    g.add_edge(1, 2, **{DIST: np.sqrt(2)})
    g.add_edge(1, 3, **{DIST: np.sqrt(2)})
    g.add_edge(3, 4, **{DIST: np.sqrt(2)})
    return g


@pytest.fixture
def f2(graph) -> flow.Flow:
    return flow.Flow(
        graph=graph, resolution=RES, alpha=ALPHA, z_delta_max=ZD_MAX, exponent=EXP
    )


@pytest.fixture
def release2() -> np.ndarray:
    return np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0], [0, 0, 0]])


def test_from_array(f):
    pass


def test_calc_z_alpha(f2: flow.Flow):
    z_alpha = f2.calc_z_alpha(node=0, child=1)
    assert z_alpha == pytest.approx(0.1763, abs=1e-2)

    z_alpha = f2.calc_z_alpha(node=3, child=4)
    assert z_alpha == pytest.approx(0.2493, abs=1e-2)


def test_calc_z_gamma(f2: flow.Flow):
    z_gamma = f2.calc_z_gamma(node=0, child=1)
    assert z_gamma == 1.0

    z_gamma = f2.calc_z_gamma(node=3, child=4)
    assert z_gamma == 2.0


def test_calc_z_delta(f2: flow.Flow):
    f2.graph.nodes[1][ZD] = 0
    z_delta = f2.calc_z_delta(node=1, child=3)
    assert z_delta == pytest.approx(0.7506, abs=1e-4)


def test_calc_direction(f2: flow.Flow):
    d = f2.calc_direction(node=1, child=3)
    assert d == pytest.approx(0.0338, abs=1e-4)

    d = f2.calc_direction(node=1, child=2)
    assert d == pytest.approx(0.9662, abs=1e-4)


def test_calc_persistence(f2: flow.Flow):
    f2.graph.nodes[0][ZD] = 0
    pers = f2.calc_persistence(parent=None, base=0, child=1)
    assert pers == 1.0

    z_delta = 10
    f2.graph.nodes[1][ZD] = z_delta
    pers = f2.calc_persistence(parent=0, base=1, child=2)
    assert pers == PERS[45] * z_delta

    f2.graph.nodes[3][ZD] = z_delta
    pers = f2.calc_persistence(parent=1, base=3, child=4)
    assert pers == PERS[90] * z_delta


def test_calc_routing(f2: flow.Flow):
    f2.graph.add_node(5, **{X: 2, Y: 1, ELEV: 5.0})
    f2.graph.add_node(6, **{X: 2, Y: 3, ELEV: 0.0})
    f2.graph.add_edge(5, 3, **{DIST: 1.0})
    f2.graph.add_edge(3, 6, **{DIST: 1.0})

    f2.graph.nodes[3][ZD] = 2.0
    f2.graph.nodes[3][REL] = 0.5
    f2.graph[5][3][FLUX] = 1.0
    f2.graph[1][3][FLUX] = 2.0

    routing = f2.calc_routing(3, 6)
    # test will fail; need to calculate routing value by hand
    assert routing == 1.0
