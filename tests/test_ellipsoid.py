import pytest
import numpy as np
from euclid.shape_classes.ellipsoid import Ellipsoid
from hypothesis import given
from hypothesis.strategies import floats


@given(floats(0.1, 1000), floats(0.1, 1000), floats(0.1, 1000))
def test_surface_area(a, b, c):
    """Check surface area against an approximate formula."""
    # Approximation from:
    # https://en.wikipedia.org/wiki/Ellipsoid#Approximate_formula
    p = 1.6075
    approx_surface = 4 * np.pi * (
        (a**p * b**p + a**p * c**p + b**p * c**p) / 3)**(1/p)

    ellipsoid = Ellipsoid(a, b, c)
    assert ellipsoid.surface_area == pytest.approx(approx_surface, rel=0.015)


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


def test_iq():
    sphere = Ellipsoid(1, 1, 1)
    assert sphere.iq == pytest.approx(1)


@given(floats(0.1, 1000), floats(0.1, 1000), floats(0.1, 1000))
def test_iq_symmetry(a, b, c):
    ellipsoid1 = Ellipsoid(a, b, c)
    ellipsoid2 = Ellipsoid(c, a, b)
    ellipsoid3 = Ellipsoid(b, c, a)
    assert ellipsoid1.iq == pytest.approx(ellipsoid2.iq)
    assert ellipsoid1.iq == pytest.approx(ellipsoid3.iq)
    assert ellipsoid2.iq == pytest.approx(ellipsoid3.iq)


@given(floats(0.1, 1000), floats(0.1, 1000), floats(0.1, 1000))
def test_inertia_tensor(a, b, c):
    ellipsoid = Ellipsoid(a, b, c)
    assert np.all(ellipsoid.inertia_tensor >= 0)

    sphere = Ellipsoid(a, a, a)
    expected = 2/5 * sphere.volume * a**2
    np.testing.assert_allclose(np.diag(sphere.inertia_tensor), expected)
