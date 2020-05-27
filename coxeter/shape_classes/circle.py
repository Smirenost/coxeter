import numpy as np
from.base_classes import Shape2D


class Circle(Shape2D):
    """A circle with the given radius.

    Args:
        radius (float):
            Radius of the circle.
        center (Sequence[float]):
            The coordinates of the center of the circle (Default
            value: (0, 0, 0)).
    """
    def __init__(self, radius, center=(0, 0, 0)):
        self._radius = radius
        self._center = np.asarray(center)

    @property
    def gsd_shape_spec(self):
        """dict: A complete description of this shape corresponding to the
        shape specification in the GSD file format as described
        `here <https://gsd.readthedocs.io/en/stable/shapes.html>`_."""
        return {'type': 'Sphere', 'diameter': 2*self._radius}

    @property
    def center(self):
        return self._center

    @center.setter
    def center(self, value):
        self._center = np.asarray(value)

    @property
    def radius(self):
        """float: Radius of the circle."""
        return self._radius

    @radius.setter
    def radius(self, radius):
        self._radius = radius

    @property
    def area(self):
        """float: The area."""
        return np.pi * self.radius**2

    @property
    def eccentricity(self):
        """float: The eccentricity. This is 0 by definition for circles."""
        return 0

    @property
    def perimeter(self):
        """float: The perimeter."""
        return 2 * np.pi * self.radius

    @property
    def circumference(self):
        """float: Alias for :meth:`~.perimeter`."""
        return self.perimeter

    @property
    def planar_moments_inertia(self):
        R"""Get the planar moments with respect to the x and y axis as well as
        the product of inertia.

        The `planar moments <https://en.wikipedia.org/wiki/Polar_moment_of_inertia>`__
        and the
        `product moment <https://en.wikipedia.org/wiki/Second_moment_of_area#Product_moment_of_area>`__
        are defined by the formulas:

        .. math::
            \begin{align}
                I_x &= {\int \int}_A y^2 dA = \frac{\pi}{4} r^4 = \frac{Ar^2}{4} \\
                I_y &= {\int \int}_A x^2 dA = \frac{\pi}{4} r^4 = \frac{Ar^2}{4}\\
                I_{xy} &= {\int \int}_A xy dA = 0 \\
            \end{align}

        These formulas are given `here https://en.wikipedia.org/wiki/List_of_second_moments_of_area`__.
        Note that the product moment is zero by symmetry.
        """  # noqa: E501
        A = self.area
        Ix = Iy = A/4 * self.radius**2
        Ixy = 0

        # Apply parallel axis theorem from the center
        Ix += A*self.center[0]**2
        Iy += A*self.center[1]**2
        Ixy += A*self.center[0]*self.center[1]
        return Ix, Iy, Ixy

    @property
    def polar_moment_inertia(self):
        """The polar moment of inertia.

        The `polar moment of inertia <https://en.wikipedia.org/wiki/Polar_moment_of_inertia>`__
        is always calculated about an axis perpendicular to the circle (i.e. the
        normal vector) placed at the centroid of the circle.

        The polar moment is computed as the sum of the two planar moments of inertia.
        """  # noqa: E501
        return np.sum(self.planar_moments_inertia[:2])

    @property
    def iq(self):
        """float: The isoperimetric quotient. This is 1 by definition for
        circles."""
        return 1
