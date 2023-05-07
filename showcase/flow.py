from geometry import Geometry
from graph import Graph
import networkx as nx
import numpy as np
from parameters import PERS, DIST, ELEV, ZD, REL, FLUX
from raster import Raster
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

        # instance of a directed (acyclic) graph
        graph = nx.DiGraph()
        nrow, ncol = array.shape
        for x in range(ncol):
            for y in range(nrow):
                # integer node index
                node_index = Raster.calc_1d_index(x, y, nrow)
                # retrieve elevation at cell x, y
                elev = array[x, y]
                if node_index not in graph:
                    # add node with attributed x, y and elevation to graph
                    graph.add_node(node_index, x=x, y=y, **{ELEV: elev})
                neighbour_indices = Raster.get_neighbour_indices(x, y)
                # iterate over cell's eight neighbour cells
                for neighbour_index in neighbour_indices:
                    neighbour_x, neighbour_y = neighbour_index
                    if Raster.inside(ncol, nrow, neighbour_x, neighbour_y):
                        n_index = Raster.calc_1d_index(neighbour_x, neighbour_y, nrow)
                        n_elev = array[neighbour_x, neighbour_y]
                        if elev > n_elev:
                            # add neighbour to graph if it is not represented yet
                            if n_index not in graph:
                                graph.add_node(
                                    n_index,
                                    x=neighbour_x,
                                    y=neighbour_y,
                                    **{ELEV: n_elev},
                                )
                            distance = Geometry.calc_distance(
                                x, y, neighbour_x, neighbour_y
                            )
                            # create edge from higher to lower cell
                            graph.add_edge(node_index, n_index, **{DIST: distance})
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
        return self.graph[node][ELEV] - self.graph[child][ELEV]

    def calc_z_delta(self, node: int, child: int) -> float:
        """Kinetic energy height"""
        z_alpha = self.calc_z_alpha(node, child)
        z_gamma = self.calc_z_gamma(node, child)
        z_delta = self.graph[node][ZD] + z_gamma - z_alpha
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
        # coordinates of parent, base and child node
        xp, yp = Graph.get_coordinates(self.graph, parent)
        xb, yb = Graph.get_coordinates(self.graph, base)
        xc, yc = Graph.get_coordinates(self.graph, child)
        angle = Geometry.calc_angle_pbc(xp, yp, xb, yb, xc, yc)
        z_delta = self.graph[base][ZD]
        return PERS[angle] * z_delta

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
        # get direction for node -> child
        direction = self.calc_direction(node, child)
        # get persistence for node -> child
        persistence = sum([self.calc_persistence(p, node, child) for p in parents])
        # incoming flux from parents
        flux = sum([p[FLUX] for p in parents])
        # add external release of base node and calculate routing
        return direction * persistence / denominator * (flux + node[REL])

    def find_release_nodes(self) -> List[int]:
        # TODO: cache?, write exceptions, move to graph
        # and generalize to any field and any minimum value
        return [n for n in self.graph if n[REL] > 0]

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
        return self.graph.copy().remove_edges_from(outside)

    def build_model(self, release: np.array) -> None:
        """Flow and mass flux calculation
        
        Results are saved to nodes and edges as attribute data
        """
        # TODO: external and internal methods directly access graph attribute
        # --> write getter and setter
        # add release to nodes
        Graph.add_data_from_array(self.graph, release)
        # find active nodes
        active = self.find_active_nodes()
        # sort topologically
        active_sorted = Graph.sort_graph(active)
        # iterate over nodes
        for node in active_sorted:
            parents = Graph.get_parents(active_sorted, node)
            children = Graph.get_children(active_sorted, node)
            # set ZD to 0 for start nodes, max of incoming for others
            if Graph.is_start_node(active_sorted, node):
                active_sorted[node][ZD] = 0
            else:
                pass
            # calculate direction, persistence, routing for sorted nodes
            # and edges
            # after calculating node and edge data for this reduced graph,
            # attach data to edges and nodes to self.graph