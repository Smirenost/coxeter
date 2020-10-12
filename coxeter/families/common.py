"""Certain common shape families that can be analytically generated."""

import os

import numpy as np

from ..shapes import ConvexPolygon
from .doi_data_repositories import _DATA_FOLDER
from .shape_family import ShapeFamily
from .tabulated_shape_family import TabulatedGSDShapeFamily


class RegularNGonFamily(ShapeFamily):
    """The family of convex regular polygons.

    This class generates the set of convex regular polygons with :math:`n`
    sides. The polygons are normalized to be unit area by default, and the
    initial vertex always lies on the :math:`x` axis (so, for example, a
    4-sided shape generated by this will look like a diamond, i.e. a square
    rotated by 45 degrees).

    The following parameters are required by this class:

      - :math:`n`: The number of vertices of the polygon
    """

    @classmethod
    def get_shape(cls, n):
        """Generate an n-gon with area 1.

        Args:
            n (int):
                The number of vertices (greater than or equal to 3).

        Returns:
             :class:`~.ConvexPolygon`: The corresponding regular polygon.
        """
        return ConvexPolygon(cls.make_vertices(n))

    @classmethod
    def make_vertices(cls, n):
        """Generate vertices of an n-gon with area 1.

        Args:
            n (int):
                An integer greater than or equal to 3.

        Returns:
            :math:`(n, 3)` :class:`numpy.ndarray` of float: The vertices of the polygon.
        """
        if n < 3:
            raise ValueError("Cannot generate an n-gon with fewer than 3 vertices.")
        r = 1  # The radius of the circle
        theta = np.linspace(0, 2 * np.pi, num=n, endpoint=False)
        pos = np.array([np.cos(theta), np.sin(theta)]).T

        # First normalize to guarantee that the limiting case of an infinite
        # number of vertices produces a circle of area r^2.
        pos /= np.sqrt(np.pi) / r

        # The area of an n-gon inscribed in a circle is given by:
        # \frac{n r^2}{2} \sin(2\pi / n)
        # The ratio of that n-gon area to its inscribed circle area is:
        a_circ_a_poly = np.pi / ((n / 2) * np.sin(2 * np.pi / n))

        # Rescale the positions so that the final shape has area 1
        pos *= np.sqrt(a_circ_a_poly)

        return pos


PlatonicFamily = TabulatedGSDShapeFamily.from_json_file(
    os.path.join(_DATA_FOLDER, "platonic.json"),
    classname="PlatonicFamily",
    docstring="""The family of Platonic solids.

The following parameters are required by this class:

    - name: The name of the Platonic solid. Options are "Cube", "Dodecahedron", \
            "Icosahedron", "Octahedron", and "Tetrahedron".
""",
)
