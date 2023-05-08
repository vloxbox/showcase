import numpy as np
import pytest
import showcase.flow as flow

N = 3
RESOLUTION = 10
ALPHA = 10
ZD_MAX = 9
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
        resolution=RESOLUTION,
        alpha=ALPHA,
        z_delta_max=ZD_MAX,
        exponent=EXP
    )

def test_from_array(f):
    pass
