from scipy.spatial import ConvexHull
import numpy as np
from .polygon import Polygon


class Polyhedron(object):
    def __init__(self, vertices, facets=None, normals=None):
        """A general polyhedron.

        If only vertices are passed in, the result is a convex polyhedron
        defined by these vertices. If facets are provided, the resulting
        polyhedron may be nonconvex.

        The polyhedron is assumed to be of unit mass and constant density.

        """
        self._vertices = np.array(vertices, dtype=np.float64)
        if facets is None:
            hull = ConvexHull(vertices)
            self._facets = [facet for facet in hull.simplices]
        else:
            # TODO: Add some sanity checks here.
            self._facets = facets

        self._normals = normals

        # For now, we're assuming convexity in determining the normal. Will
        # need to relax this eventually with a ray-based algorithm. Note that
        # we could use a cross product to compute the normal, but we have no
        # way to determine the directionality with that approach.
        # TODO: Stop assuming convexity.
        # self._equations = np.empty((len(self.facets), 4))
        # print("facet Shape: ", len(self.facets))
        # print("Shape: ", self._equations.shape)
        # for i, facet in enumerate(self.facets):
            # # v0 = self.vertices[facet[0]]
            # # v1 = self.vertices[facet[1]]
            # # v2 = self.vertices[facet[2]]
            # # normal = np.cross(v2 - v1, v1 - v1)
            # normal = np.mean(self.vertices[facet]) - self.center
            # print(normal)
            # self._equations[i, :3] = normal / np.linalg.norm(normal)
            # self._equations[i, 3] = normal.dot(self.vertices[facet[0]])

    def _find_equations(self):
        """Find equations of facets.

        This function makes no guarantees about the direction of the normal it
        chooses."""
        self._equations = np.empty((len(self.facets), 4))
        for i, facet in enumerate(self.facets):
            v0 = self.vertices[facet[0]]
            v1 = self.vertices[facet[1]]
            v2 = self.vertices[facet[2]]
            normal = np.cross(v2 - v1, v1 - v0)
            self._equations[i, :3] = normal / np.linalg.norm(normal)
            self._equations[i, 3] = normal.dot(self.vertices[facet[0]])

    def _find_neighbors(self):
        """Find neighbors of facets."""
        # First enumerate all edges of each neighbor. We include both
        # directions of the edges for comparison.
        facet_edges = []
        for facet in self.facets:
            forward_edges = set(zip(*np.stack((facet, np.roll(facet, 1)))))
            reverse_edges = set(zip(*np.stack((facet, np.roll(facet, -1)))))
            facet_edges.append(forward_edges.union(reverse_edges))

        # Find any facets that share neighbors.
        num_facets = len(facet_edges)
        self._connectivity_graph = np.zeros((num_facets, num_facets))
        for i in range(num_facets):
            for j in range(i+1, num_facets):
                if len(facet_edges[i].intersection(facet_edges[j])) > 0:
                    self._connectivity_graph[i, j] = 1
                    # For symmetry
                    # self._connectivity_graph[j, i] = 1

    def merge_facets(self, tolerance=1e-6):
        """Merge facets of a polyhedron.

        For convex polyhedra, facets will automatically be merged to an
        appropriate degree.  However, the merging of facets must be based on a
        tolerance (we may need to provide two such parameters depending on how
        we perform the merge), so we need to expose this method to allow the
        user to redo the merge with a different tolerance."""
        self._find_equations()
        self._find_neighbors()

        # Test if these are coplanar.
        num_facets = len(self.facets)
        merge_graph = np.zeros((num_facets, num_facets))
        for i, j in zip(*np.where(self._connectivity_graph)):
            if np.allclose(self._equations[i, :], self._equations[j, :]) or \
                    np.allclose(self._equations[i, :], -self._equations[j, :]):
                merge_graph[i, j] = 1

        # Merge selected facets.
        new_facets = []
        remaining_facets = np.arange(merge_graph.shape[0]).tolist()
        for i in remaining_facets:
            cur_set = set(self.facets[i])
            for j, in np.where(merge_graph[i]):
                cur_set = cur_set.union(self.facets[j])
                remaining_facets.remove(j)
            new_facets.append(np.array(list(cur_set)))
        self._facets = new_facets

    @property
    def vertices(self):
        """Get the vertices of the polyhedron."""
        return self._vertices

    @property
    def facets(self):
        """Get the polyhedron's facets."""
        return self._facets

    @property
    def volume(self):
        """Get or set the polyhedron's volume (setting rescales vertices)."""
        # pass
        # print("verts: ", self.vertices)
        # print(self._equations[:, 3])
        # print(self.get_facet_area())
        # return np.sum(self._equations[:, 3]*self.get_facet_area())/3
        # Arbitrary choice, use the first vertex in the face.
        ds = np.sum(self._normals *
                    self.vertices[[x[0] for x in self.facets]], axis=1)
        return np.sum(ds*self.get_facet_area())/3

    @volume.setter
    def volume(self, value):
        pass

    def get_facet_area(self, facets=None):
        """Get the total surface area of a set of facets.

        Args:
            facets (int, sequence, or None):
                The index of a facet or a set of facet indices for which to
                find the area. If None, finds the area of all facets (Default
                value: None).

        Returns:
            list: The area of each facet.
        """
        if facets is None:
            facets = range(len(self.facets))

        areas = np.empty(len(facets))
        for i, facet_index in enumerate(facets):
            facet = self.facets[facet_index]
            poly = Polygon(self.vertices[facet])
            areas[i] = poly.area

        return areas

    @property
    def surface_area(self):
        """The surface area."""
        return np.sum(self.get_facet_area())

    @property
    def inertia_tensor(self):
        """The inertia tensor.

        Computed using the method described in
        https://www.tandfonline.com/doi/abs/10.1080/2151237X.2006.10129220
        """
        try:
            return self._inertia_tensor
        except AttributeError:
            centered_vertices = self.vertices - self.center
            simplices = centered_vertices[self.faces]

            volumes = np.abs(np.linalg.det(simplices)/6)

            fxx = lambda triangles: triangles[:, 1]**2 + triangles[:, 2]**2 # noqa
            fxy = lambda triangles: -triangles[:, 0]*triangles[:, 1] # noqa
            fxz = lambda triangles: -triangles[:, 0]*triangles[:, 2] # noqa
            fyy = lambda triangles: triangles[:, 0]**2 + triangles[:, 2]**2 # noqa
            fyz = lambda triangles: -triangles[:, 1]*triangles[:, 2] # noqa
            fzz = lambda triangles: triangles[:, 0]**2 + triangles[:, 1]**2 # noqa

            def compute(f):
                return f(simplices[:, 0, :]) + f(simplices[:, 1, :]) + \
                    f(simplices[:, 2, :]) + f(simplices[:, 0, :] +
                                              simplices[:, 1, :] +
                                              simplices[:, 2, :])

            Ixx = (compute(fxx)*volumes/20).sum()
            Ixy = (compute(fxy)*volumes/20).sum()
            Ixz = (compute(fxz)*volumes/20).sum()
            Iyy = (compute(fyy)*volumes/20).sum()
            Iyz = (compute(fyz)*volumes/20).sum()
            Izz = (compute(fzz)*volumes/20).sum()

            self._inertia_tensor = np.array([[Ixx, Ixy, Ixz],
                                            [Ixy,   Iyy, Iyz],
                                            [Ixz,   Iyz,   Izz]])

            return self._inertia_tensor

    @property
    def center(self):
        """Get or set the polyhedron's centroid (setting rescales vertices)."""
        return np.mean(self.vertices, axis=0)

    @center.setter
    def center(self, value):
        self._vertices += (np.asarray(value) - self.center)

    @property
    def insphere_radius(self):
        """Get or set the polyhedron's insphere radius (setting rescales
        vertices)."""
        pass

    @insphere_radius.setter
    def insphere_radius(self, value):
        pass

    @property
    def circumsphere_radius(self):
        """Get or set the polyhedron's circumsphere radius (setting rescales
        vertices)."""
        pass

    @circumsphere_radius.setter
    def circumsphere_radius(self, value):
        pass

    @property
    def asphericity(self):
        """The asphericity."""
        pass

    @property
    def iq(self):
        """The isoperimetric quotient."""
        pass

    @property
    def tau(self):
        """The sphericity measure defined in
        https://www.sciencedirect.com/science/article/pii/0378381284800199."""
        pass

    @property
    def facet_neighbors(self):
        """An Nx2 NumPy array containing indices of pairs of neighboring
        facets."""
        pass

    @property
    def vertex_neighbors(self):
        """An Nx2 NumPy array containing indices of pairs of neighboring
        vertex."""
        pass
