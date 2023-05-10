from .geometry import Geometry
from .parameters import X, Y, ELEV, DIST, FLUX
from .raster import Raster
import itertools as it
import networkx as nx
import numpy as np
from typing import List, Tuple


class Graph:
    @staticmethod
    def from_dem(array: np.array):
        graph = nx.DiGraph()
        nrow, ncol = array.shape
        for x in range(ncol):
            for y in range(nrow):
                # integer node index
                node_index = Raster.calc_1d_index(x, y, ncol)
                # retrieve elevation at cell x, y
                elev = array[y, x]
                if node_index not in graph:
                    # add node with attributes x, y and elevation to graph
                    graph.add_node(node_index, **{X: x, Y: y, ELEV: elev})
                # iterate over cell's eight neighbour cells
                for neighbour_index in Raster.get_neighbour_indices(x, y):
                    n_x, n_y = neighbour_index
                    if Raster.inside(ncol, nrow, *neighbour_index):
                        n_index = Raster.calc_1d_index(*neighbour_index, ncol)
                        n_elev = array[n_y, n_x]
                        if elev > n_elev:
                            # add neighbour to graph if it is not represented yet
                            if n_index not in graph:
                                graph.add_node(
                                    n_index,
                                    **{X: n_x, Y: n_y, ELEV: n_elev},
                                )
                            distance = Geometry.calc_distance(x, y, *neighbour_index)
                            # create edge from higher to lower cell
                            graph.add_edge(
                                node_index, n_index, **{DIST: distance, FLUX: 0}
                            )
        return graph

    @staticmethod
    def find_all_successors(graph: nx.DiGraph, source) -> List:
        """Find all successors of one or multiple nodes"""
        successors = list(nx.edge_dfs(graph, source, orientation="original"))
        if successors:
            *n, _ = zip(*(successors))
            return list(set(it.chain.from_iterable(n)))
        return [source]

    @staticmethod
    def find_all_start_nodes(graph: nx.DiGraph) -> List:
        return [node for node, deg in graph.in_degree() if deg == 0]

    @staticmethod
    def is_start_node(graph: nx.DiGraph, node) -> bool:
        if graph.in_degree[node] == 0:
            return True
        return False

    @staticmethod
    def sort_graph(graph: nx.DiGraph) -> List:
        """Sort graph by topology (high to low)"""
        return list(nx.topological_sort(graph))

    @staticmethod
    def get_children(graph: nx.DiGraph, node: int) -> List:
        return list(dict(graph.succ[node]))

    @staticmethod
    def get_parents(graph: nx.DiGraph, node: int) -> List:
        return list(dict(graph.pred[node]))

    @staticmethod
    def get_coordinates(graph: nx.DiGraph, node: int) -> Tuple:
        return graph.nodes[node][X], graph.nodes[node][Y]

    @staticmethod
    def add_data_from_array(graph: nx.DiGraph, array: np.array, field: str) -> None:
        """Add data from numpy array to graph nodes"""
        # identify nodes by index
        nrow, ncol = array.shape
        for x in range(ncol):
            for y in range(nrow):
                idx = Raster.calc_1d_index(x, y, ncol)
                if idx in graph:
                    # check order of coordinates when retrieving data from array
                    graph.nodes[idx][field] = array[y, x]

    @staticmethod
    def to_array(graph: nx.DiGraph, field: str, rows: int, cols: int, fill_value=np.nan) -> np.ndarray:
        """Create array of data in field"""
        array = np.empty((rows, cols))
        array[:] = fill_value
        for node in graph:
            if field in graph.nodes[node]:
                x, y = graph.nodes[node][X], graph.nodes[node][Y]
                array[y, x] = graph.nodes[node][field]
        return array
