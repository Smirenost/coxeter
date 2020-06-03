import numpy as np
import pytest
from hypothesis import given
from hypothesis.extra.numpy import arrays
from hypothesis.strategies import floats

from coxeter.shape_classes.ellipsoid import Ellipsoid
from coxeter.shape_classes.utils import translate_inertia_tensor


@given(floats(0.1, 1000), floats(0.1, 1000), floats(0.1, 1000))
def test_surface_area(a, b, c):
    """Check surface area against an approximate formula."""
    # Approximation from:
    # https://en.wikipedia.org/wiki/Ellipsoid#Approximate_formula
    p = 1.6075
    approx_surface = 4 * np.pi * (
        (a**p * b**p + a**p * c**p + b**p * c**p) / 3)**(1 / p)

    ellipsoid = Ellipsoid(a, b, c)
    assert ellipsoid.surface_area == pytest.approx(approx_surface, rel=0.015)


@given(floats(0.1, 1000), floats(0.1, 1000), floats(0.1, 1000))
def test_volume(a, b, c):
    ellipsoid = Ellipsoid(1, 1, 1)
    ellipsoid.a = a
    ellipsoid.b = b
    ellipsoid.c = c
    assert ellipsoid.volume == 4 / 3 * np.pi * a * b * c


def test_earth():
    """Approximate Earth's volume and surface area."""
    # Uses data (in meters) from GRS 80:
    # https://en.wikipedia.org/wiki/Geodetic_Reference_System_1980
    a = b = 6378137
    c = 6356752.314
    earth_volume = 1.08e21  # or so, m^3
    earth_surface = 510.1e12  # or so, m^2
    earth = Ellipsoid(a, b, c)
    assert earth.volume == pytest.approx(earth_volume, rel=1.01)
    assert earth.surface_area == pytest.approx(earth_surface, rel=1.01)


@given(floats(0.1, 1000))
def test_iq(r):
    sphere = Ellipsoid(r, r, r)
    assert sphere.iq == pytest.approx(1)


@given(floats(0.1, 1000), floats(0.1, 1000), floats(0.1, 1000))
def test_iq_symmetry(a, b, c):
    ellipsoid1 = Ellipsoid(a, b, c)
    ellipsoid2 = Ellipsoid(c, a, b)
    ellipsoid3 = Ellipsoid(b, c, a)
    assert ellipsoid1.iq == pytest.approx(ellipsoid2.iq)
    assert ellipsoid1.iq == pytest.approx(ellipsoid3.iq)
    assert ellipsoid2.iq == pytest.approx(ellipsoid3.iq)


@given(floats(0.1, 1000), floats(0.1, 1000), floats(0.1, 1000),
       arrays(np.float64, (3, ), elements=floats(-10, 10, width=64),
              unique=True))
def test_inertia_tensor(a, b, c, center):
    # First just test a sphere.
    ellipsoid = Ellipsoid(a, a, a)
    assert np.all(ellipsoid.inertia_tensor >= 0)

    volume = ellipsoid.volume
    expected = [2 / 5 * volume * a**2] * 3
    np.testing.assert_allclose(np.diag(ellipsoid.inertia_tensor), expected)

    ellipsoid.center = center
    expected = translate_inertia_tensor(center, np.diag(expected), volume)
    np.testing.assert_allclose(ellipsoid.inertia_tensor, expected)


@given(floats(0.1, 1000), floats(0.1, 1000), floats(0.1, 1000))
def test_is_inside(a, b, c):
    ellipsoid = Ellipsoid(a, b, c)
    points_inside = np.array([[a, 0, 0], [-a, 0, 0],
                              [0, b, 0], [0, -b, 0],
                              [0, 0, c], [0, 0, -c]])
    assert all(ellipsoid.is_inside(points_inside))
    assert all(ellipsoid.is_inside(points_inside / 2))
    assert not any(ellipsoid.is_inside(points_inside * 1.1))


def test_center():
    """Test getting and setting the center."""
    ellipsoid = Ellipsoid(1, 2, 3)
    assert all(ellipsoid.center == (0, 0, 0))

    center = (1, 1, 1)
    ellipsoid.center = center
    assert all(ellipsoid.center == center)
