import numpy as np
import pytest

from kuva_geometry.ellipsoid import (
    Earth,
    geodetic_to_xyz,
    ray_Earth_intersection,
    ray_ellipsoid_intersection,
    xyz_to_geodetic,
)


def test_geoid_to_ecef_roundtrip():
    """Test that geod to ECEF conversions work both ways"""

    lat, lon, h = np.deg2rad(28.0), np.deg2rad(-17.0), 737.0
    to_xyz = geodetic_to_xyz(lat, lon, h)
    back_to_geo = xyz_to_geodetic(*to_xyz)
    error = np.abs(np.array(back_to_geo) - np.array((28, -17, 737)))
    assert np.all(error < 1e-3)


def test_ray_ellipsoid_intersection_uses_forward_root_for_inside_origin():
    origin = np.array([0.0, 0.0, 0.0])
    direction = np.array([1.0, 0.0, 0.0])

    intersection = ray_ellipsoid_intersection(origin, direction, Earth)
    intersections = ray_ellipsoid_intersection(origin, np.array([direction]), Earth)

    expected = np.array([Earth.major_axis, 0.0, 0.0])
    assert np.allclose(intersection, expected)
    assert np.allclose(intersections[0], expected)


def test_ray_ellipsoid_intersection_rejects_away_pointing_rays():
    origin = np.array([7000000.0, 0.0, 0.0])
    direction = np.array([1.0, 0.0, 0.0])

    with pytest.raises(ValueError, match="forward direction"):
        ray_ellipsoid_intersection(origin, direction, Earth)

    with pytest.raises(ValueError, match="forward direction"):
        ray_ellipsoid_intersection(origin, np.array([direction]), Earth)


@pytest.mark.parametrize(
    "origin",
    [
        np.array([[0.0, 0.0, 0.0]]),
        np.array([[0.0], [0.0], [0.0]]),
    ],
)
def test_ray_ellipsoid_intersection_rejects_invalid_origin_shapes(origin):
    direction = np.array([1.0, 0.0, 0.0])

    with pytest.raises(ValueError, match="Ray origin must be a 1d array of length 3"):
        ray_ellipsoid_intersection(origin, direction, Earth)


@pytest.mark.parametrize(
    "directions",
    [
        np.array([[1.0, 0.0], [0.0, 1.0]]),
        np.array([[1.0], [0.0], [0.0]]),
    ],
)
def test_ray_ellipsoid_intersection_rejects_invalid_direction_shapes(directions):
    origin = np.array([0.0, 0.0, 0.0])

    with pytest.raises(
        ValueError, match=r"Ray directions must have shape \(3,\) or \(n_rays, 3\)"
    ):
        ray_ellipsoid_intersection(origin, directions, Earth)


@pytest.mark.filterwarnings("ignore:invalid value encountered in sqrt:RuntimeWarning")
def test_ray_ellipsoid_intersection_rejects_rays_that_miss_ellipsoid():
    origin = np.array([0.0, 0.0, Earth.minor_axis + 1000.0])
    direction = np.array([1.0, 0.0, 0.0])

    with pytest.raises(ValueError, match="forward direction"):
        ray_ellipsoid_intersection(origin, direction, Earth)


def test_ray_ellipsoid_intersection_accepts_batch_inputs():
    origin = np.array([7000000.0, 0.0, 0.0])
    directions = np.array([[-1.0, 0.0, 0.0], [-0.9, 0.1, 0.0]])

    intersections = ray_ellipsoid_intersection(origin, directions, Earth)
    earth_intersections = ray_Earth_intersection(origin, directions)

    assert intersections.shape == (2, 3)
    assert np.allclose(intersections, earth_intersections)
