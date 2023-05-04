import networkx
import numpy as np

from typing import Tuple


class Network:
    """Digital elevation model structured as directed acyclic graph

    This class structures a digital elevation model (DEM)
    as directed acyclic graph using the networkx package.
    Advantages:
        - Less loops (and therefore increased performance)
        - Built-in parent/child relationships, less index calculations
        - Built-in functions such as sorting by topography, shortest path
    """

    def __init__(self, array: np.ndarray) -> None:
        """Constructor

        TODO: Add raster resolution (cell size) for calculating distances

        Args:
            array (np.ndarray): DEM as 2D numpy array

        Returns:
            None
        """
        self.array = array

    @property
    def shape(self) -> Tuple[int, int]:
        """Number of rows and columns of DEM array"""
        return self.array.shape

    @property
    def graph(self) -> networkx.DiGraph:
        """Create graph from DEM array

        Cells are stored as nodes in a directed acyclic graph.
        Edges connect nodes from parent node (higher elevation)
        to child node (lower elevation)

        TODO:
            - refactor function, e.g. distance calculation
            - add row and column indices as data to nodes
            - add distance between nodes as data to edges

        Args:
            None

        Returns:
            networkx.DiGraph: Graph representation of DEM
        """

        g = networkx.DiGraph()
        nrow, ncol = self.shape
        for x in range(ncol):
            for y in range(nrow):
                node_index = x + y * nrow
                if node_index not in g:
                    g.add_node(node_index)
                elev = self.array[x, y]
                neighbour_indices = self._get_neighbour_indices(x, y)
                for neighbour_index in neighbour_indices:
                    nx, ny = neighbour_index
                    if self._inside(nx, ny):
                        n_index = nx + ny * nrow
                        n_elev = self.array[nx, ny]
                        if elev > n_elev:
                            if n_index not in g:
                                g.add_node(n_index)
                            g.add_edge(node_index, n_index)
        return g

    def _get_neighbour_indices(self, x: int, y: int) -> np.ndarray:
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

    def _inside(self, x: int, y: int) -> bool:
        """Check if cell indices are out of bound

        Args:
            x (int): column index
            y (int): row index

        Returns:
            bool: Returns True if cell indices belong to cells on DEM array
        """
        nrow, ncol = self.shape
        if 0 <= x < ncol and 0 <= y < nrow:
            return True
        return False
