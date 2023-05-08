from .parameters import X, Y
from .raster import Raster
import itertools as it
import networkx as nx
import numpy as np
from typing import List, Tuple


class Graph:
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
                idx = Raster.calc_1d_index(x, y, nrow)
                # check order of coordinates when retrieving data from array
                graph.nodes[idx][field] = array[y, x]

    @staticmethod
    def to_array(graph: nx.DiGraph, field: str, rows: int, cols: int) -> np.ndarray:
        """Create array of data in field"""
        pass
