import pytest
import numpy as np
import numpy.testing as npt
import rowan
from coxeter.shape_classes.polygon import Polygon
from coxeter.shape_classes.convex_polygon import ConvexPolygon
from hypothesis import given, example, assume
from hypothesis.strategies import floats
from hypothesis.extra.numpy import arrays
from conftest import get_valid_hull


def polygon_from_hull(verts):
    """Try to generate a polygon from a hull, and fail gracefully (in the
    context of Hypothesis) if the hull is poorly formed."""
    try:
        poly = Polygon(verts)
    except AssertionError:
        # Don't worry about failures caused by bad hulls that cause failures
        # for the simple polygon test.
        assume(False)
    return poly


# Need to declare this outside the fixture so that it can be used in multiple
# fixtures (pytest does not allow fixtures to be called).
def get_square_points():
    return np.asarray([[0, 0, 0],
                       [0, 1, 0],
                       [1, 1, 0],
                       [1, 0, 0]])


@pytest.fixture
def square_points():
    return get_square_points()


@pytest.fixture
def square():
    return Polygon(get_square_points())


@pytest.fixture
def convex_square():
    return ConvexPolygon(get_square_points())


@pytest.fixture
def ones():
    return np.ones((4, 2))


def test_2d_verts(square_points):
    """Try creating object with 2D vertices."""
    square_points = square_points[:, :2]
    Polygon(square_points)


def test_duplicate_points(square_points):
    """Ensure that running with any duplicate points produces a warning."""
    square_points = np.vstack((square_points, square_points[[0]]))
    with pytest.raises(ValueError):
        Polygon(square_points)


def test_identical_points(ones):
    """Ensure that running with identical points produces an error."""
    with pytest.raises(ValueError):
        Polygon(ones)


def test_reordering(square_points, square):
    """Test that vertices can be reordered appropriately."""
    npt.assert_equal(square.vertices, square_points)

    square.reorder_verts(True)
    # We need the roll because the algorithm attempts to minimize unexpected
    # vertex shuffling by keeping the original 0 vertex in place.
    reordered_points = np.roll(np.flip(square_points, axis=0), shift=1, axis=0)
    npt.assert_equal(square.vertices, reordered_points)

    # Original vertices are clockwise, so they'll be flipped on construction if
    # we specify the normal. Note that we MUST use the Convexpolygon class,
    # since Polygon will not sort by default.
    square = ConvexPolygon(square_points, normal=[0, 0, 1])
    npt.assert_equal(square.vertices, reordered_points)

    square.reorder_verts(True)
    npt.assert_equal(square.vertices, square_points)


def test_area(square_points):
    """Test area calculation."""
    # Shift to ensure that the negative areas are subtracted as needed.
    points = np.asarray(square_points) + 2
    square = Polygon(points)
    assert square.signed_area == 1
    assert square.area == 1

    # Ensure that area is signed.
    square.reorder_verts(True)
    assert square.signed_area == -1
    assert square.area == 1


def test_set_area(square):
    """Test setting area."""
    square.area = 2
    assert np.isclose(square.area, 2)


def test_center(square, square_points):
    """Test centering the polygon."""
    assert np.all(square.center == np.mean(square_points, axis=0))
    square.center = [0, 0, 0]
    assert np.all(square.center == [0, 0, 0])


def test_moment_inertia(square):
    """Test moment of inertia calculation."""

    # First test the default values.
    square.center = (0, 0, 0)
    assert np.allclose(square.planar_moments_inertia, (1/12, 1/12, 0))
    assert np.isclose(square.polar_moment_inertia, 1/6)

    # Use hypothesis to validate the simple parallel axis theorem.
    @given(arrays(np.float64, (3, ), elements=floats(-5, 5, width=64),
                  unique=True))
    def testfun(center):
        # Just move in the plane.
        center[2] = 0
        square.center = center

        assert np.isclose(square.polar_moment_inertia,
                          1/6 + square.area*np.dot(center, center))

    testfun()


def test_inertia_tensor(square):
    """Test the inertia tensor calculation."""

    square.center = (0, 0, 0)
    assert np.sum(square.inertia_tensor > 1e-6) == 1
    assert square.inertia_tensor[2, 2] == 1/6

    # Validate yz plane.
    rotation = rowan.from_axis_angle([0, 1, 0], np.pi/2)
    rotated_verts = rowan.rotate(rotation, square.vertices)
    rotated_square = ConvexPolygon(rotated_verts)
    assert np.sum(rotated_square.inertia_tensor > 1e-6) == 1
    assert rotated_square.inertia_tensor[0, 0] == 1/6

    # Validate xz plane.
    rotation = rowan.from_axis_angle([1, 0, 0], np.pi/2)
    rotated_verts = rowan.rotate(rotation, square.vertices)
    rotated_square = ConvexPolygon(rotated_verts)
    assert np.sum(rotated_square.inertia_tensor > 1e-6) == 1
    assert rotated_square.inertia_tensor[1, 1] == 1/6

    # Validate translation along each axis.
    delta = 2
    area = square.area
    for i in range(3):
        translation = [0]*3
        translation[i] = delta
        translated_verts = square.vertices + translation
        translated_square = ConvexPolygon(translated_verts)
        offdiagonal_tensor = translated_square.inertia_tensor.copy()
        diag_indices = np.diag_indices(3)
        offdiagonal_tensor[diag_indices] = 0
        assert np.sum(offdiagonal_tensor > 1e-6) == 0
        expected_diagonals = [0, 0, 1/6]
        for j in range(3):
            if i != j:
                expected_diagonals[j] += area*delta*delta
        assert np.allclose(np.diag(translated_square.inertia_tensor),
                           expected_diagonals)


def test_nonplanar(square_points):
    """Ensure that nonplanar vertices raise an error."""
    with pytest.raises(ValueError):
        square_points[0, 2] += 1
        Polygon(square_points)


@given(arrays(np.float64, (4, 2), elements=floats(1, 5, width=64),
              unique=True))
@example(np.array([[1, 1],
                   [1, 1.00041707],
                   [2.78722762, 1],
                   [2.72755193, 1.32128906]]))
def test_reordering_convex(points):
    """Test that vertices can be reordered appropriately."""
    hull = get_valid_hull(points)
    assume(hull)

    verts = points[hull.vertices]
    poly = polygon_from_hull(points[hull.vertices])
    assert np.all(poly.vertices[:, :2] == verts)


@given(arrays(np.float64, (4, 2), elements=floats(-5, 5, width=64),
              unique=True))
@example(np.array([[1, 1],
                   [1, 1.00041707],
                   [2.78722762, 1],
                   [2.72755193, 1.32128906]]))
def test_convex_area(points):
    """Check the areas of various convex sets."""
    hull = get_valid_hull(points)
    assume(hull)

    poly = polygon_from_hull(points[hull.vertices])
    assert np.isclose(hull.volume, poly.area)


@given(random_quat=arrays(np.float64, (4, ), elements=floats(-1, 1, width=64)))
def test_rotation_signed_area(random_quat):
    """Ensure that rotating does not change the signed area."""
    assume(not np.all(random_quat == 0))
    random_quat = rowan.normalize(random_quat)
    rotated_points = rowan.rotate(random_quat, get_square_points())
    poly = Polygon(rotated_points)
    assert np.isclose(poly.signed_area, 1)

    poly.reorder_verts(clockwise=True)
    assert np.isclose(poly.signed_area, -1)


@given(arrays(np.float64, (4, 2), elements=floats(-5, 5, width=64),
              unique=True))
def test_set_convex_area(points):
    """Test setting area of arbitrary convex sets."""
    hull = get_valid_hull(points)
    assume(hull)

    poly = polygon_from_hull(points[hull.vertices])
    original_area = poly.area
    poly.area *= 2
    assert np.isclose(poly.area, 2*original_area)


def test_triangulate(square):
    triangles = [tri for tri in square._triangulation()]
    assert len(triangles) == 2

    all_vertices = [tuple(vertex) for triangle in triangles for vertex in
                    triangle]
    assert len(set(all_vertices)) == 4

    assert not np.all(np.asarray(triangles[0]) == np.asarray(triangles[1]))


def get_unit_area_ngon(n):
    """Compute vertices of a regular n-gon of area 1. Useful for constructing
    simple tests of some of the "containing sphere" calculations."""
    r = 1  # The radius of the circle
    theta = np.linspace(0, 2*np.pi, num=n, endpoint=False)
    pos = np.array([np.cos(theta), np.sin(theta)])

    # First normalize to guarantee that the limiting case of an infinite number
    # of vertices produces a circle of area r^2.
    pos /= (np.sqrt(np.pi)/r)

    # Area of an n-gon inscribed in a circle
    # A_poly = ((n*r**2)/2)*np.sin(2*np.pi/n)
    # A_circ = np.pi*r**2
    # pos *= np.sqrt(A_circ/A_poly)
    A_circ_over_A_poly = np.pi/((n/2)*np.sin(2*np.pi/n))
    pos *= np.sqrt(A_circ_over_A_poly)

    return pos.T


def test_bounding_circle_radius_regular_polygon():
    for i in range(3, 10):
        vertices = get_unit_area_ngon(i)
        rmax = np.max(np.linalg.norm(vertices, axis=-1))

        poly = Polygon(vertices)
        center, radius = poly.bounding_circle

        assert np.isclose(rmax, radius)
        assert np.allclose(center, 0)


@given(arrays(np.float64, (3, 2), elements=floats(-5, 5, width=64),
              unique=True))
def test_bounding_circle_radius_random_hull(points):
    hull = get_valid_hull(points)
    assume(hull)

    vertices = points[hull.vertices]
    poly = Polygon(vertices)

    # For an arbitrary convex polygon, the furthest vertex from the origin is
    # an upper bound on the bounding sphere radius, but need not be the radius
    # because the ball need not be centered at the centroid.
    rmax = np.max(np.linalg.norm(poly.vertices, axis=-1))
    center, radius = poly.bounding_circle
    assert radius <= rmax + 1e-6

    poly.center = [0, 0, 0]
    center, radius = poly.bounding_circle
    assert radius <= rmax + 1e-6


@given(points=arrays(np.float64, (3, 2), elements=floats(-5, 5, width=64),
                     unique=True),
       rotation=arrays(np.float64, (4, ), elements=floats(-1, 1, width=64)))
def test_bounding_circle_radius_random_hull_rotation(points, rotation):
    """Test that rotating vertices does not change the bounding radius."""
    assume(not np.all(rotation == 0))

    hull = get_valid_hull(points)
    assume(hull)

    vertices = points[hull.vertices]
    poly = Polygon(vertices)

    rotation = rowan.normalize(rotation)
    rotated_vertices = rowan.rotate(rotation, poly.vertices)
    poly_rotated = Polygon(rotated_vertices)

    _, radius = poly.bounding_circle
    _, rotated_radius = poly_rotated.bounding_circle
    assert np.isclose(radius, rotated_radius)


def test_circumcircle():
    for i in range(3, 10):
        vertices = get_unit_area_ngon(i)
        rmax = np.max(np.linalg.norm(vertices, axis=-1))

        poly = Polygon(vertices)
        center, radius = poly.circumcircle

        assert np.isclose(rmax, radius)
        assert np.allclose(center, 0)


def test_incircle_from_center(convex_square):
    center, radius = convex_square.incircle_from_center
    assert np.all(center == convex_square.center)
    assert radius == 0.5
