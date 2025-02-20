"""Geometry utilities to find the footprint associated with an in orbit camera"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import quaternion
import shapely
from kuva_geometry import ellipsoid, geometry

if TYPE_CHECKING:
    from .sections_l0 import Camera, Frame


def get_sensor_corner_rays(
    camera: Camera,
    position: np.ndarray,
    orientation: quaternion.quaternion,
    use_negative_sensor_plane: bool = False,
):
    """Get the rays emanating from a camera associated with the corners of the sensor

    Parameters
    ----------
    camera
        Camera intrinsic parameters
    position
        The position of the satellite in ECEF coordinates expressed in meters (3 values)
    orientation
        Quaternion describing the orientation of the satellite wrt ECEF
    use_negative_sensor_plane, optional
        Whether to use the negative sensor plane to calculate the rays, by default False

    Returns
    -------
        The vectors that join the back nodal point to the sensor corners.
    """
    ray_origin, rays = geometry.get_sensor_corner_rays(
        np.array(position),
        orientation,
        camera.focal_distance.to("meters").magnitude,
        camera.width.to("meters").magnitude,
        camera.height.to("meters").magnitude,
        use_negative_sensor_plane,
    )

    return ray_origin, rays


def get_sensor_rays(
    sensor_coords: np.ndarray,
    camera: Camera,
    position: np.ndarray,
    orientation: quaternion.quaternion,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Produce an array with the ray vectors for a collections of sensor coords.

    Sensor coords are measured from the center of the sensor and are valid within
    [-0.5, 0.5]^2.

    Parameters
    ----------
    sensor_coords
        A rank-2 tensor of dimension (n_sensor_coords, 2)
    camera
        Camera intrinsic parameters
    position
        The position of the satellite in ECEF coordinates expressed in meters (3 values)
    orientation
        Quaternion describing the orientation of the satellite wrt ECEF

    Returns
    -------
    The position from which the rays emanate, i.e. the camera position and rank 2 tensor
    of dimensions (n_sensor_coords, 3) describing the direction vector of the rays.
    """
    rays = geometry.get_sensor_rays(
        sensor_coords,
        position,
        orientation,
        camera.focal_distance.to("meters").magnitude,
        camera.width.to("meters").magnitude,
        camera.height.to("meters").magnitude,
        use_negative_sensor_plane=True,
    )

    return position, rays


def frame_ray_Earth_intersections(
    sensor_coords: np.ndarray, frame: Frame, camera: Camera
) -> list[shapely.Point]:
    """
    Return the intersecton of camera ray with the WGS84 ellipsoid.

    Parameters
    ----------
    sensor_coords
        The coordinates of the ray we are interested on. Within sensor coords range
        between +- 0.5 on both axis.
    frame
        Information about how the frame was taken. Namely camera orientation and
        position.
    camera
        The camera parameters

    Returns
    -------
        Intersection of camera rays on the Earth
    """
    sat_pos, sat_ecef_orientation = frame.position.numpy, frame.sat_ecef_orientation

    # Make sure the order is correct, i.e. begin from the right-hand side!
    # The process is the same as for how we calculate homographies.
    orientation = sat_ecef_orientation * camera.sensor_wrt_sat_axis_quaternion

    _, rays = get_sensor_rays(sensor_coords, camera, sat_pos, orientation)

    rays = rays / np.sqrt((rays**2).sum(axis=1))[:, None]

    intersections = [
        shapely.Point(*ellipsoid.ray_Earth_intersection(sat_pos, rays[idx]))
        for idx in range(rays.shape[0])
    ]

    return intersections


def frame_footprint(
    frame: Frame,
    camera: Camera,
    use_negative_sensor_plane: bool = False,
) -> shapely.Polygon:
    """Find the footprint on the ground associated with the corners rays of a camera

    Parameters
    ----------
    frame
        Information about how the frame was taken. Namely camera orientation and
        position.
    camera
        The camera parameters
    use_negative_sensor_plane, optional
        Whether to use the negative sensor plane to calculate the rays, by default False

    Returns
    -------
        The footprint on the ground as a polygon
    """
    sat_pos, sat_ecef_orientation = frame.position.numpy, frame.sat_ecef_orientation

    orientation = sat_ecef_orientation * camera.sensor_wrt_sat_axis_quaternion

    _, sensor_corners_ray = get_sensor_corner_rays(
        camera, sat_pos, orientation, use_negative_sensor_plane
    )

    sensor_corners_ray = (
        sensor_corners_ray / np.sqrt((sensor_corners_ray**2).sum(axis=1))[:, None]
    )

    footprint = [
        ellipsoid.ray_Earth_intersection(sat_pos, sensor_corners_ray[idx])
        for idx in range(sensor_corners_ray.shape[0])
    ]

    # Polygons are ordered X,Y despite the CRS being lat, long i.e. x,y. If you
    # leave the points in the order they come in the 4326 CRS things will break.
    footprint = shapely.Polygon(footprint)

    return footprint
