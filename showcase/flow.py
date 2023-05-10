from .geometry import Geometry
from .graph import Graph
from .parameters import PERS, DIST, ELEV, ZD, REL, FLUX, DIR
from .raster import Raster
import networkx as nx
import numpy as np
from typing import List


class Flow:
    """Class for calculation of flow and mass transport

    An instance of Flow can be created from a digital elevation
    model (DEM) in form of a numpy array. DEMs are represented
    as directed acyclic graphs (DAC) in which nodes with a higher
    elevation are connected to their neighbours at lower elevations
    by a directed edge ("an arrow").

    The flow and mass transport calculation is structured as follows:

    1. Calculation of the kinetic energy height ("delta_z")
    2. Calculation of persistence values
    3. Calculation of terrain-based routing (multiple flow direction algorithm
        by Holmgren)
    4. Calculation of mass flow from the steps above

    The methodology is thoroughly described in the reference list of the README.md file
    """

    def __init__(
        self,
        graph: nx.DiGraph,
        resolution: float,
        alpha: float,
        z_delta_max: float,
        exponent: float,
    ) -> None:
        self.graph = graph
        self.resolution = resolution
        self.alpha = alpha
        self.z_delta_max = z_delta_max
        self.exponent = exponent

    @classmethod
    def from_array(
        cls,
        array: np.ndarray,
        resolution: float,
        alpha: float,
        z_delta_max: float,
        exponent: float,
    ):
        """Create Flow instance from DEM array and raster resolution

        Cells are stored as nodes in a directed acyclic graph.
        Edges connect nodes from parent node (higher elevation)
        to child node (lower elevation)

        Args:
            array (np.ndarray): Numpy elevation array
            resolution (float): Raster resolution (cell size)
            alpha (float): maximum runout angle
            z_delta_max (float): maximum kinetic energy height
            exponent (float): exponent for Holmgren flow direction

        Returns:
            cls
        """

        graph = Graph.from_dem(array)
        return cls(graph, resolution, alpha, z_delta_max, exponent)

    def calc_z_alpha(self, node: int, child: int) -> float:
        """Loss function

        Reduction of energy height due to friction losses
        """
        edge = self.graph[node][child]
        tan_alpha = np.tan(np.deg2rad(self.alpha))
        return edge[DIST] * self.resolution * tan_alpha

    def calc_z_gamma(self, node: int, child: int) -> float:
        """Change in potential energy"""
        return self.graph.nodes[node][ELEV] - self.graph.nodes[child][ELEV]

    def calc_z_delta(self, node: int, child: int) -> float:
        """Kinetic energy height"""
        z_alpha = self.calc_z_alpha(node, child)
        z_gamma = self.calc_z_gamma(node, child)
        z_delta = self.graph.nodes[node][ZD] + z_gamma - z_alpha
        return max(0, min(z_delta, self.z_delta_max))

    def calc_direction(self, node: int, child: int) -> float:
        """Multiple flow direction (Holmgren)"""
        # TODO: instead of calculating denominator and direction every time,
        # attach them as data to node and edge, and query if data is available;
        # if not available, compute
        children = Graph.get_children(self.graph, node)
        tan_phis, directions = [], []
        if children:
            for c in children:
                distance = self.graph[node][c][DIST] * self.resolution
                z_gamma = self.calc_z_gamma(node, c)
                # TODO: double check equation
                phi = np.arctan(z_gamma / distance) + np.deg2rad(90)
                # TODO: double check equation
                tan_phi = np.tan(phi / 2)
                tan_phis.append(tan_phi)
            denominator = sum([i**self.exponent for i in tan_phis])
            for i in tan_phis:
                direction = max(0, i**self.exponent / denominator)
                directions.append(direction)
        direction_dict = dict(zip(children, directions))
        return direction_dict[child]

    def calc_persistence(self, parent: int, base: int, child: int) -> float:
        """Persistence

        Taking into account inertia of debris flow
        """
        z_delta = self.graph.nodes[base][ZD]
        # special case: no parent (start cell), persistence = 1
        if Graph.is_start_node(self.graph, base) or z_delta == 0:
            return 1.0
        # coordinates of parent, base and child node
        xp, yp = Graph.get_coordinates(self.graph, parent)
        xb, yb = Graph.get_coordinates(self.graph, base)
        xc, yc = Graph.get_coordinates(self.graph, child)
        angle = Geometry.calc_angle_pbc(xp, yp, xb, yb, xc, yc)
        return PERS[round(angle)] * z_delta

    def calc_routing(self, node: int, child: int) -> float:
        """Mass flow calculation"""
        parents = Graph.get_parents(self.graph, node)
        children = Graph.get_children(self.graph, node)
        # directions and persistence values for all children
        dirs = [self.calc_direction(node, c) for c in children]
        pers = [
            sum([self.calc_persistence(p, node, c) for p in parents]) for c in children
        ]
        denominator = sum([d * p for d, p in zip(dirs, pers)])
        # special case: denominator == .0
        if denominator == .0:
            return .0
        # get direction for node -> child
        direction = self.calc_direction(node, child)
        # get persistence for node -> child
        persistence = sum([self.calc_persistence(p, node, child) for p in parents])
        # incoming flux from parents
        if Graph.is_start_node(self.graph, node):
            flux = 0
        else:
            flux = sum([self.graph[p][node][FLUX] for p in parents])
        # add external release of base node and calculate routing
        return (
            direction * persistence / denominator * (flux + self.graph.nodes[node][REL])
        )

    def find_release_nodes(self) -> List[int]:
        # TODO: cache?, write exceptions, move to graph
        # and generalize to any field and any minimum value
        return [n for n in self.graph if self.graph.nodes[n][REL] > 0]

    def find_active_nodes(self) -> nx.DiGraph:
        """Graph size reduction

        Limits calculation to cells that participate in flow
        """
        # identify release nodes (REL > 0)
        rel_nodes = self.find_release_nodes()
        # identify all successors of release nodes
        successors = Graph.find_all_successors(self.graph, rel_nodes)
        # rewrite to avoid loop
        outside = [n for n in self.graph if n not in successors]
        copy = self.graph.copy()
        copy.remove_nodes_from(outside)
        return copy

    def build_model(self, release: np.array) -> None:
        """Flow and mass flux calculation

        Results are saved to nodes and edges as attribute data
        """
        # TODO: external and internal methods directly access graph attribute
        # --> write getter and setter
        # add release to nodes
        Graph.add_data_from_array(self.graph, release, REL)
        # find active nodes
        active = self.find_active_nodes()
        # sort topologically
        active_sorted = Graph.sort_graph(active)
        # iterate over nodes
        for node in active_sorted:
            parents = Graph.get_parents(active, node)
            children = Graph.get_children(active, node)
            # set ZD to 0 for start nodes, max of incoming for others
            if Graph.is_start_node(active, node):
                z_delta = 0
            else:
                z_delta = max([self.graph[p][node][ZD] for p in parents])
            self.graph.nodes[node][ZD] = z_delta
            # calculate direction, persistence, routing for sorted nodes
            # outgoing edges
            if children:
                # set delta_z before persistence --> requires separate loops
                for child in children:
                    edge = self.graph[node][child]
                    edge[ZD] = self.calc_z_delta(node, child)
                    edge[DIR] = self.calc_direction(node, child)
                for child in children:
                    self.graph[node][child][FLUX] = self.calc_routing(node, child)
            # assign FLUX value to node
            self.graph.nodes[node][FLUX] = self.graph.nodes[node][REL]
            if parents:
                self.graph.nodes[node][FLUX] += sum([self.graph[p][node][FLUX] for p in parents])
            