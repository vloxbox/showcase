import numpy as np


class Raster:
    @staticmethod
    def get_neighbour_indices(x: int, y: int) -> np.ndarray:
        """Get indices of neighbouring cells

        Used for loop over DEM array when constructing graph

        Args:
            x (int): column index
            y (int): row index

        Returns:
            np.ndarray: Array containing index tuples of eight neighbour cells
        """
        return np.array(
            [
                (x - 1, y - 1),
                (x, y - 1),
                (x + 1, y - 1),
                (x - 1, y),
                (x + 1, y),
                (x - 1, y + 1),
                (x, y + 1),
                (x + 1, y + 1),
            ]
        )

    @staticmethod
    def inside(ncol: int, nrow: int, x: int, y: int) -> bool:
        """Check if cell indices are out of bound

        Args:
            ncol (int): number of columns
            nrow (int): number of rows
            x (int): column index
            y (int): row index

        Returns:
            bool: Returns True if cell indices belong to cells on DEM array
        """
        if 0 <= x < ncol and 0 <= y < nrow:
            return True
        return False

    @staticmethod
    def calc_1d_index(x: int, y: int, ncol: int) -> int:
        """One-dimensional index on 2D array"""
        return y + x * ncol
