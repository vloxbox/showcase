import numpy as np
import pytest
from showcase.geometry import Geometry


def test_calc_distance():
    assert Geometry.calc_distance(0, 0, 1, 1) == pytest.approx(np.sqrt(2), abs=1e-6)
    assert Geometry.calc_distance(0, 0, 0, -1) == pytest.approx(1, abs=1e-6)


def test_calc_angle_pbc():
    cells = {
        0: (0, 0),
        1: (1, 0),
        2: (2, 0),
        3: (0, 1),
        4: (1, 1),
        5: (2, 1),
        6: (0, 2),
        7: (1, 2),
        8: (2, 2),
    }

    assert Geometry.calc_angle_pbc(*cells[0], *cells[4], *cells[8]) == pytest.approx(
        0, abs=1e-3
    )
    assert Geometry.calc_angle_pbc(*cells[0], *cells[4], *cells[7]) == pytest.approx(
        45, abs=1e-3
    )
    assert Geometry.calc_angle_pbc(*cells[0], *cells[4], *cells[6]) == pytest.approx(
        90, abs=1e-3
    )
    assert Geometry.calc_angle_pbc(*cells[0], *cells[4], *cells[5]) == pytest.approx(
        45, abs=1e-3
    )
    assert Geometry.calc_angle_pbc(*cells[0], *cells[4], *cells[3]) == pytest.approx(
        135, abs=1e-3
    )
    assert Geometry.calc_angle_pbc(*cells[0], *cells[4], *cells[2]) == pytest.approx(
        90, abs=1e-3
    )
    assert Geometry.calc_angle_pbc(*cells[0], *cells[4], *cells[1]) == pytest.approx(
        135, abs=1e-3
    )
    assert Geometry.calc_angle_pbc(*cells[0], *cells[4], *cells[0]) == pytest.approx(
        180, abs=1e-3
    )
    assert Geometry.calc_angle_pbc(*cells[1], *cells[4], *cells[6]) == pytest.approx(
        45, abs=1e-3
    )
