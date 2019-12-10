from scipy.spatial import ConvexHull
import numpy as np
from .polygon import Polygon
from scipy.sparse.csgraph import connected_components


def _facet_to_edges(facet, reverse=False):
    """Convert a facet (a sequence of vertices) into a sequence of edges
    (tuples).

    Args:
        facet (array-like):
            A facet composed of vertex indices.
        reverse (bool):
            Whether to return the edges in reverse.
    """
    shift = 1 if reverse else -1
    return list(zip(*np.stack((facet, np.roll(facet, shift)))))


class Polyhedron(object):
    def __init__(self, vertices, facets):
        """A three-dimensional polytope.

        A polyhedron is defined by a set of vertices and a set of facets
        composed of the vertices. On construction, the facets are reordered
        counterclockwise with respect to an outward normal. The polyhedron
        provides various standard geometric calculations, such as volume and
        surface area. Most features of the polyhedron can be accessed via
        properties, including the plane equations defining the facets and the
        neighbors of each facet.

        .. note::
            For the purposes of calculations like moments of inertia, the
            polyhedron is assumed to be of constant, unit density.

        Args:
            vertices (:math:`(N, 3)` :class:`numpy.ndarray`):
                The vertices of the polyhedron.
            facets (:math:`(N, 3)` :class:`numpy.ndarray`):
                The facets of the polyhedron.
        """
        self._vertices = np.array(vertices, dtype=np.float64)
        self._facets = [facet for facet in facets]
        self.sort_facets()

    def _find_equations(self):
        """Find the plane equations of the polyhedron facets."""
        self._equations = np.empty((len(self.facets), 4))
        for i, facet in enumerate(self.facets):
            # The direction of the normal is selected such that vertices that
            # are already ordered counterclockwise will point outward.
            normal = np.cross(
                self.vertices[facet[2]] - self.vertices[facet[1]],
                self.vertices[facet[0]] - self.vertices[facet[1]])
            normal /= np.linalg.norm(normal)
            self._equations[i, :3] = normal
            self._equations[i, 3] = normal.dot(self.vertices[facet[0]])

    def _find_neighbors(self):
        """Find neighbors of facets. Note that facets must be ordered before
        this method is called, so internal usage should only happen after
        :math:`~.sort_facets` is called."""
        # First enumerate all edges of each neighbor. We include both
        # directions of the edges for comparison.
        facet_edges = [set(_facet_to_edges(f) +
                           _facet_to_edges(f, True)) for f in self.facets]

        # Find any facets that share neighbors.
        self._neighbors = [[] for _ in range(self.num_facets)]
        for i in range(self.num_facets):
            for j in range(i+1, self.num_facets):
                if len(facet_edges[i].intersection(facet_edges[j])) > 0:
                    self._neighbors[i].append(j)
                    self._neighbors[j].append(i)
            self._neighbors[i] = np.array(self._neighbors[i])

    def merge_facets(self, atol=1e-8, rtol=1e-5):
        """Merge coplanar facets to a given tolerance.

        Whether or not facets should be merged is determined using
        :func:`numpy.allclose` to compare the plane equations of neighboring
        facets. Connected components of mergeable facets are then merged into
        a single facet.  This method can be safely called many times with
        different tolerances, however, the operation is destructive in the
        sense that merged facets cannot be recovered. Users wishing to undo a
        merge to attempt a less expansive merge must build a new polyhedron.
        """
        # Construct a graph where connectivity indicates merging, then identify
        # connected components to merge.
        merge_graph = np.zeros((self.num_facets, self.num_facets))
        for i in range(self.num_facets):
            for j in self._neighbors[i]:
                eq1, eq2 = self._equations[[i, j]]
                if np.allclose(eq1, eq2, atol=atol, rtol=rtol) or \
                        np.allclose(eq1, -eq2, atol=atol, rtol=rtol):
                    merge_graph[i, j] = 1

        _, labels = connected_components(merge_graph, directed=False,
                                         return_labels=True)
        new_facets = [set() for _ in range(len(np.unique(labels)))]
        for i, facet in enumerate(self.facets):
            new_facets[labels[i]].update(facet)

        self._facets = [np.asarray(list(f)) for f in new_facets]
        self.sort_facets()

    @property
    def neighbors(self):
        """list(:class:`numpy.ndarray`): A list where the :math:`i`th element
        is an array of indices of facets that are neighbors of facet :math:`i`.
        """
        return self._neighbors

    @property
    def normals(self):
        """:math:`(N, 3)` :class:`numpy.ndarray`: The normal vectors to each
        facet."""
        return self._equations[:, :3]

    @property
    def num_vertices(self):
        """int: The number of vertices."""
        return self.vertices.shape[0]

    @property
    def num_facets(self):
        """int: The number of facets."""
        return len(self.facets)

    def sort_facets(self):
        """Ensure that all facets are ordered such that the normals are
        counterclockwise and point outwards.

        This algorithm proceeds in four steps. First, it ensures that each
        facet is ordered in either clockwise or counterclockwise order such
        that edges can be found from the sequence of the vertices in each
        facet. Next, it calls the neighbor finding routine to establish with
        facets are neighbors. Then, it performs a breadth-first search,
        reorienting facets to match the orientation of the first facet.
        Finally, it computes the signed volume to determine whether or not all
        the normals need to be flipped.
        """
        # We first ensure that facet vertices are sequentially ordered by
        # constructing a Polygon and updating the facet (in place), which
        # enables finding neighbors.
        for facet in self.facets:
            facet[:] = np.asarray([
                np.where(np.all(self.vertices == vertex, axis=1))[0][0]
                for vertex in Polygon(self.vertices[facet],
                                      planar_tolerance=1e-4).vertices
            ])
        self._find_neighbors()

        # The initial facet sets the order of the others.
        visited_facets = []
        remaining_facets = [0]
        while len(remaining_facets):
            current_facet = remaining_facets[-1]
            visited_facets.append(current_facet)
            remaining_facets.pop()

            # Search for common edges between pairs of facets, then check the
            # ordering of the edge to determine relative facet orientation.
            current_edges = _facet_to_edges(self.facets[current_facet])
            for neighbor in self._neighbors[current_facet]:
                if neighbor in visited_facets:
                    continue
                remaining_facets.append(neighbor)

                # Two facets can only share a single edge (otherwise they would
                # be coplanar), so we can break as soon as we find the
                # neighbor. Flip the neighbor if the edges are identical.
                for edge in _facet_to_edges(self.facets[neighbor]):
                    if edge in current_edges:
                        self._facets[neighbor] = self._facets[neighbor][::-1]
                        break
                    elif edge[::-1] in current_edges:
                        break
                visited_facets.append(neighbor)

        # Now compute the signed area and flip all the orderings if the area is
        # negative.
        self._find_equations()
        if self.volume < 0:
            for i in range(len(self.facets)):
                self._facets[i] = self._facets[i][::-1]
                self._equations[i] *= -1

    @property
    def vertices(self):
        """:math:`(N, 3)` :class:`numpy.ndarray`: Get the vertices of the
        polyhedron."""
        return self._vertices

    @property
    def facets(self):
        """list(:class:`numpy.ndarray`): Get the polyhedron's facets."""
        return self._facets

    @property
    def volume(self):
        """float: Get or set the polyhedron's volume (setting rescales
        vertices)."""
        ds = self._equations[:, 3]
        return np.sum(ds*self.get_facet_area())/3

    @volume.setter
    def volume(self, new_volume):
        scale_factor = (new_volume/self.volume)**(1/3)
        self._vertices *= scale_factor
        self._equations[:, 3] *= scale_factor

    def get_facet_area(self, facets=None):
        """Get the total surface area of a set of facets.

        Args:
            facets (int, sequence, or None):
                The index of a facet or a set of facet indices for which to
                find the area. If None, finds the area of all facets (Default
                value: None).

        Returns:
            :class:`numpy.ndarray`: The area of each facet.
        """
        if facets is None:
            facets = range(len(self.facets))
        elif type(facets) is int:
            facets = [facets]

        areas = np.empty(len(facets))
        for i, facet_index in enumerate(facets):
            facet = self.facets[facet_index]
            poly = Polygon(self.vertices[facet], planar_tolerance=1e-4)
            areas[i] = poly.area

        return areas

    @property
    def surface_area(self):
        """float: Get the surface area."""
        return np.sum(self.get_facet_area())

    def _triangulation(self):
        """Generate a triangulation of the surface of the polyhedron.

        This algorithm constructs Polygons from each of the facets and then
        triangulates each of these to provide a total triangulation.
        """
        for facet in self.facets:
            poly = Polygon(self.vertices[facet], planar_tolerance=1e-4)
            yield from poly._triangulation()

    @property
    def inertia_tensor(self):
        """float: Get the inertia tensor computed about the center of mass
        (uses the algorithm described in :cite:`Kallay2006`)."""
        simplices = np.array(list(self._triangulation())) - self.center

        volumes = np.abs(np.linalg.det(simplices)/6)

        def triangle_integrate(f):
            R"""Compute integrals of the form :math:`\int\int\int f(x, y, z)
            dx dy dz` over a set of triangles. Omits a factor of v/20."""
            fv1 = f(simplices[:, 0, :])
            fv2 = f(simplices[:, 1, :])
            fv3 = f(simplices[:, 2, :])
            fvsum = (f(simplices[:, 0, :] +
                       simplices[:, 1, :] +
                       simplices[:, 2, :]))
            return np.sum((volumes/20)*(fv1 + fv2 + fv3 + fvsum))

        Ixx = triangle_integrate(lambda t: t[:, 1]**2 + t[:, 2]**2)
        Ixy = triangle_integrate(lambda t: -t[:, 0]*t[:, 1])
        Ixz = triangle_integrate(lambda t: -t[:, 0]*t[:, 2])
        Iyy = triangle_integrate(lambda t: t[:, 0]**2 + t[:, 2]**2)
        Iyz = triangle_integrate(lambda t: -t[:, 1]*t[:, 2])
        Izz = triangle_integrate(lambda t: t[:, 0]**2 + t[:, 1]**2)

        return np.array([[Ixx, Ixy, Ixz],
                         [Ixy,   Iyy, Iyz],
                         [Ixz,   Iyz,   Izz]])

    @property
    def center(self):
        """float: Get or set the polyhedron's centroid (setting rescales
        vertices)."""
        return np.mean(self.vertices, axis=0)

    @center.setter
    def center(self, value):
        self._vertices += (np.asarray(value) - self.center)
        self._find_equations()

    @property
    def circumsphere_radius(self):
        """float: Get or set the polyhedron's circumsphere radius (setting
        rescales vertices)."""
        return np.linalg.norm(self.vertices - self.center, axis=1).max()

    @circumsphere_radius.setter
    def circumsphere_radius(self, new_radius):
        scale_factor = new_radius/self.circumsphere_radius
        self._vertices *= scale_factor
        self._equations[:, 3] *= scale_factor

    @property
    def iq(self):
        """float: The isoperimetric quotient."""
        V = self.volume
        S = self.surface_area
        return np.pi * 36 * V * V / (S * S * S)

    def get_dihedral(self, a, b):
        """Get the dihedral angle between a pair of facets.

        The dihedral is computed from the dot product of the facet normals.

        Args:
            a (int):
                The index of the first facet.
            b (int):
                The index of the secondfacet.

        Returns:
            float: The dihedral angle in radians.
        """
        if b not in self.neighbors[a]:
            raise ValueError("The two facets are not neighbors.")
        n1, n2 = self._equations[[a, b], :3]
        return np.arccos(np.dot(-n1, n2))


class ConvexPolyhedron(Polyhedron):
    def __init__(self, vertices):
        """A convex polyhedron.

        A convex polyhedron is defined as the convex hull of its vertices. The
        class is a simple extension of :class:`~.Polyhedron` that builds the
        facets from the simplices of the convex hull. This class also includes
        various additional properties that can be used to characterize the
        geometric features of the polyhedron.

        Args:
            vertices (:math:`(N, 3)` :class:`numpy.ndarray`):
                The vertices of the polyhedron.
        """
        hull = ConvexHull(vertices)
        super(ConvexPolyhedron, self).__init__(vertices, hull.simplices)
        self.merge_facets()

    @property
    def mean_curvature(self):
        R"""float: The mean curvature
        :math:`R = \sum_i (1/2) L_i (\pi - \phi_i) / (4 \pi)` with edge lengths
        :math:`L_i` and dihedral angles :math:`\phi_i` (see :cite:`Irrgang2017`
        for more information).
        """
        R = 0
        for i in range(self.num_facets):
            for j in self.neighbors[i]:
                # Don't double count neighbors.
                if j < i:
                    continue
                phi = self.get_dihedral(i, j)
                # Include both directions for one facet to get a unique edge.
                f1 = set(_facet_to_edges(self.facets[i]))
                f2 = set(_facet_to_edges(self.facets[j]) +
                         _facet_to_edges(self.facets[j], reverse=True))
                edge = list(f1.intersection(f2))
                assert len(edge) == 1
                edge = edge[0]
                edge_vert = self.vertices[edge[0]] - self.vertices[edge[1]]
                length = np.linalg.norm(edge_vert)
                R += length * (np.pi - phi)
        return R / (8 * np.pi)

    @property
    def tau(self):
        R"""float: The parameter :math:`tau = \frac{S}{4\pi R^2}` defined in
        :cite:`Naumann19841` that is closely related to the Pitzer acentric
        factor. This quantity appears relevant to the third and fourth virial
        coefficient for hard polyhedron fluids.
        """
        R = self.mean_curvature
        return 4*np.pi*R*R/self.surface_area

    @property
    def asphericity(self):
        """float: The asphericity as defined in :cite:`Irrgang2017`."""
        return self.mean_curvature*self.surface_area/(3*self.volume)
