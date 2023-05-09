import numpy as np


class Geometry:
    @staticmethod
    def calc_distance(x1: int, y1: int, x2: int, y2: int) -> int:
        """Euclidean 2D distance between two cells"""
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    @staticmethod
    def calc_angle_pbc(xp: int, yp: int, xb: int, yb: int, xc: int, yc: int) -> float:
        """Calculate angle [deg] between parent -> base -> child"""
        v1 = Geometry.unit_vector((xb - xp, yb - yp))
        v2 = Geometry.unit_vector((xc - xb, yc - yb))
        angle = np.arccos(np.clip(np.dot(v1, v2), -1.0, 1.0))
        return np.rad2deg(angle)

    @staticmethod
    def unit_vector(vector):
        return vector / np.linalg.norm(vector)
