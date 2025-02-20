"""Functions to work with ellipsoids and ellipsoidal coordinates."""

from dataclasses import dataclass
from math import atan2

import numpy as np
from sympy import Matrix, cos, lambdify, sin, solve, sqrt, symbols

from .constants import EARTH_SEMIMAJOR_AXIS, EARTH_SEMIMINOR_AXIS

# Symbols
# 𝜑: latitude
# 𝜆: longitude
# h: radial coordinate
# a: semi-major axis e
# e: eccentricity


@dataclass
class Ellipsoid:
    """An ellipsoid usually used as an approximation to the shape of the Earth.

    Attributes
    ----------
    major_axis
    minor_axis
    """

    major_axis: float
    minor_axis: float

    @property
    def eccentricity(self) -> float:
        """Return ellipsoid eccentricity."""
        return np.sqrt((self.major_axis**2 - self.minor_axis**2) / self.major_axis**2)


Earth = Ellipsoid(EARTH_SEMIMAJOR_AXIS, EARTH_SEMIMINOR_AXIS)


def xyz_to_ellipsoid(
    x: float,
    y: float,
    z: float,
    ellipsoid: Ellipsoid,
    tol: float | None = 1e-12,
) -> tuple[float, float, float]:
    """
    Transforms cartesian coordinates (x, y, z) into geodetic (longitude, latitude,
    elevation) coordinates.

    Parameters
    ----------
    x (meter)
       First component of the cartesian target coordinates
    y (meter)
       Second component of the cartesian target coordinates
    z (meter)
       Third component of the cartesian target coordinates
    tol
       Minimal change between two successive values of lon for the optimization loop to
       converge

    Returns
    -------
    lat (degree)
       Latitude of the target on the ellispoid
    lon (degree)
       Longitude of the target on the ellipsoid
    h (meter)
       Elevation of the target.
    """
    a = ellipsoid.major_axis
    e = ellipsoid.eccentricity

    𝜆 = atan2(y, x)

    # initialize variables
    p = np.sqrt((x**2) + (y**2))
    𝜑_old = atan2(z, p * (1 - e**2))

    converged = False
    𝜑_new = 0.0  # Just here to stop Ruff from complaining about unboud vars
    h = 0.0  # Same as before
    while not converged:
        # update parameters
        N = a / (np.sqrt(1 - (e**2) * np.sin(𝜑_old) ** 2))
        h = p / np.cos(𝜑_old) - N
        𝜑_new = atan2(z, p * (1 - (N / (N + h)) * e**2))
        # convergence criteria
        converged = np.abs(𝜑_old - 𝜑_new) < tol
        # new step
        𝜑_old = 𝜑_new

    𝜑 = 𝜑_new

    return np.rad2deg(𝜑), np.rad2deg(𝜆), h


def xyz_to_geodetic(
    x: float,
    y: float,
    z: float,
    tol: float | None = 1e-12,
):
    """Turn ECEF coordinates into geodetic coordinates.

    Returns
    -------
    lat (degree)
       Latitude of the target on the ellispoid
    lon (degree)
       Longitude of the target on the ellipsoid
    h (meter)
       Elevation of the target.
    """
    return xyz_to_ellipsoid(x, y, z, Earth, tol)


def _get_coord_functions_and_jacobian():
    𝜑, 𝜆, h, a, e = symbols("𝜑, 𝜆, h, a, e")

    N = a / sqrt(1 - (e * sin(𝜑)) ** 2)
    x = (N + h) * cos(𝜑) * cos(𝜆)
    y = (N + h) * cos(𝜑) * sin(𝜆)
    z = ((1 - e**2) * N + h) * sin(𝜑)

    coords = Matrix([x, y, z])
    vars_ = Matrix([𝜑, 𝜆, h])

    jacobian = coords.jacobian(vars_)

    basis_vectors_𝜑 = lambdify([𝜑, 𝜆, h, a, e], jacobian[:, 0], modules="numpy")
    basis_vectors_𝜆 = lambdify([𝜑, 𝜆, h, a, e], jacobian[:, 1], modules="numpy")
    basis_vectors_h = lambdify([𝜑, 𝜆, h, a, e], jacobian[:, 2], modules="numpy")

    coords = lambdify([𝜑, 𝜆, h, a, e], coords)

    return coords, [basis_vectors_𝜑, basis_vectors_𝜆, basis_vectors_h]


_coords, _basis_vector = _get_coord_functions_and_jacobian()


def ellipsoidal_to_xyz(
    𝜑: np.ndarray, 𝜆: np.ndarray, h: np.ndarray, ellipsoid: Ellipsoid
) -> np.ndarray:
    """
    Transform ellipsoidal coordinates to cartesian coordinates.

    All angular units are expected in radians.

    Parameters
    ----------
    𝜑
        Latitude, that is, angle subtended between the point and equator.
    𝜆
        Longitude
    h
        Elevation over the ellipsoid.
    ellipsoid
        The ellipsoid we are dealing with
    """
    major_axis, ecc = ellipsoid.major_axis, ellipsoid.eccentricity
    return _coords(𝜑, 𝜆, h, major_axis, ecc).squeeze()


def geodetic_to_xyz(𝜑: np.ndarray, 𝜆: np.ndarray, h: np.ndarray) -> np.ndarray:
    """
    Transform Earth geodetic coordinates to ECEF coordinates

    All angular units are expected in radians.

    Parameters
    ----------
    𝜑
        Latitude, that is, angle subtended between the point and equator.
    𝜆
        Longitude
    h
        Elevation over the ellipsoid.
    """
    major_axis, ecc = Earth.major_axis, Earth.eccentricity
    return _coords(𝜑, 𝜆, h, major_axis, ecc).squeeze()


def basis_at_point(
    𝜑: float, 𝜆: float, h: float, ellipsoid: Ellipsoid
) -> list[Ellipsoid]:
    """
    Returns the basis function for ellipsoidal coordinates.

    All angular units are expected in radians.

    Parameters
    ----------
    𝜑
        Latitude, that is, angle subtended between the point and equator.
    𝜆
        Longitude
    h
        Elevation over the ellipsoid.
    ellipsoid
        The ellipsoid we are dealing with
    """
    major_axis, ecc = ellipsoid.major_axis, ellipsoid.eccentricity

    basis_vectors_𝜑 = _basis_vector[0](𝜑, 𝜆, h, major_axis, ecc).squeeze()
    basis_vectors_𝜑 = basis_vectors_𝜑 / np.sqrt(np.sum(basis_vectors_𝜑**2))

    basis_vectors_𝜆 = _basis_vector[1](𝜑, 𝜆, h, major_axis, ecc).squeeze()
    basis_vectors_𝜆 = basis_vectors_𝜆 / np.sqrt(np.sum(basis_vectors_𝜆**2))

    basis_vectors_h = _basis_vector[2](𝜑, 𝜆, h, major_axis, ecc).squeeze()
    basis_vectors_h = basis_vectors_h / np.sqrt(np.sum(basis_vectors_h**2))

    return [basis_vectors_𝜆, basis_vectors_𝜑, basis_vectors_h]


def _solve_ray_ellipsoid_intersection():
    # Symbols
    # a: semimajor axis of the ellipsoid
    # b: semiminor axis of the ellipsoid
    # t: parametrizes position along the line
    # u,v,w: parametrize the ray direction
    # x0,y0,z0: parametrize the ray origin
    a, b, t, u, v, w, x0, y0, z0 = symbols("a, b, t, u, v, w, x0, y0, z0")

    ray_origin = Matrix([x0, y0, z0])
    ray_direction = Matrix([u, v, w])

    line = ray_origin + t * ray_direction

    # We want to solve the following equation == 0
    ts = solve((line[0] / a) ** 2 + (line[1] / a) ** 2 + (line[2] / b) ** 2 - 1, t)

    ts_first = lambdify([a, b, u, v, w, x0, y0, z0], ts[0], modules="numpy")
    ts_second = lambdify([a, b, u, v, w, x0, y0, z0], ts[1], modules="numpy")

    return ts_first, ts_second


_cached_ray_ellipsoid_solution = _solve_ray_ellipsoid_intersection()


def ray_ellipsoid_intersection(
    ray_origin: np.ndarray, ray_direction: np.ndarray, ellipsoid: Ellipsoid
) -> np.ndarray:
    """Calculate the intersection of a ray and an ellipsoid

    Parameters
    ----------
    ray_origin
        Origin point of ray
    ray_direction
        Direction of ray
    ellipsoid
        Ellipsoid to calculate intersection with

    Returns
    -------
        Intersection of a ray and ellipsoid
    """
    t_1 = _cached_ray_ellipsoid_solution[0](
        ellipsoid.major_axis,
        ellipsoid.minor_axis,
        *ray_direction,
        *ray_origin,
    )
    t_2 = _cached_ray_ellipsoid_solution[1](
        ellipsoid.major_axis,
        ellipsoid.minor_axis,
        *ray_direction,
        *ray_origin,
    )

    t_sol = min(t_1, t_2)

    return ray_origin + t_sol * ray_direction


def ray_Earth_intersection(
    ray_origin: np.ndarray, ray_direction: np.ndarray
) -> np.ndarray:
    """Calculate where a ray intersects with the Earth"""
    return ray_ellipsoid_intersection(ray_origin, ray_direction, Earth)


def basis_at_geoid(𝜑: float, 𝜆: float, h: float):
    """Returns the basis function for Earth coordinates"""
    return basis_at_point(𝜑, 𝜆, h, Earth)
