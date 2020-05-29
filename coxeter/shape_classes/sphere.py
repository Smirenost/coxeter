"""Defines an circle."""

import numpy as np
from .utils import translate_inertia_tensor
from.base_classes import Shape3D


class Sphere(Shape3D):
    """A sphere with the given radius.

    Args:
        radius (float):
            Radius of the sphere.
        center (Sequence[float]):
            The coordinates of the center of the circle (Default
            value: (0, 0, 0)).
    """

    def __init__(self, radius, center=(0, 0, 0)):
        self._radius = radius
        self._center = np.asarray(center)

    @property
    def gsd_shape_spec(self):
        """dict: Get a `complete GSD specification <shapes>`_."""  # noqa: D401
        return {'type': 'Sphere', 'diameter': 2 * self._radius}

    @property
    def center(self):
        """:math:`(3, )` :class:`numpy.ndarray` of float: Get or set the centroid of the shape."""  # noqa: E501
        return self._center

    @center.setter
    def center(self, value):
        """:math:`(3, )` :class:`numpy.ndarray` of float: Get or set the centroid of the shape."""  # noqa: E501
        self._center = np.asarray(value)

    @property
    def radius(self):
        """float: Get or set the radius of the sphere."""
        return self._radius

    @radius.setter
    def radius(self, radius):
        self._radius = radius

    @property
    def volume(self):
        """float: Get the volume of the sphere."""
        return (4 / 3) * np.pi * self.radius**3

    @property
    def surface_area(self):
        """float: Get the surface area."""
        return 4 * np.pi * self.radius**2

    @property
    def inertia_tensor(self):
        """float: Get the inertia tensor. Assumes constant density of 1."""
        V = self.volume
        Ixx = V * 2 / 5 * self.radius**2
        inertia_tensor = np.diag([Ixx, Ixx, Ixx])
        return translate_inertia_tensor(
            self.center, inertia_tensor, self.volume)

    @property
    def iq(self):
        """float: The isoperimetric quotient.

        This is 1 by definition for spheres.
        """
        return 1

    def is_inside(self, points):
        """Determine whether a set of points are contained in this sphere.

        .. note::

            Points on the boundary of the shape will return :code:`True`.

        Args:
            points (:math:`(N, 3)` :class:`numpy.ndarray`):
                The points to test.

        Returns:
            :math:`(N, )` :class:`numpy.ndarray`:
                Boolean array indicating which points are contained in the
                sphere.
        """
        points = np.atleast_2d(points)
        return np.linalg.norm(points, axis=-1) <= self.radius
