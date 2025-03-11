import numpy as np
import quaternion

from kuva_geometry import geometry


def test_camera_pointing_up():
    """Test that a camera pointing up has a central ray pointing in the same
    direction.
    """
    dcm = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    dcm = dcm / np.linalg.norm(dcm, axis=1)

    rays = geometry.get_sensor_rays(
        sensor_coords=np.array([[0, 0]]),
        position=np.array((0, 0, 0)),
        orientation=quaternion.from_rotation_matrix(dcm),
        focal_distance=1.0,
        sensor_width=0.1,
        sensor_height=0.1,
    )
    assert np.allclose(rays[0], (0, 0, 1))


def test_ray_direction_should_not_depend_on_pos():
    """Moving where the camera is should have zero impact on where the rays
    are pointing at."""
    dcm = np.array([[1, 0, -1], [0, 1, 0], [1, 0, 1]])
    dcm = dcm / np.linalg.norm(dcm, axis=1)

    rays_1 = geometry.get_sensor_rays(
        sensor_coords=np.array([[0, 0]]),
        position=np.array((0, 0, 0)),
        orientation=quaternion.from_rotation_matrix(dcm),
        focal_distance=1.0,
        sensor_width=0.1,
        sensor_height=0.1,
    )
    rays_2 = geometry.get_sensor_rays(
        sensor_coords=np.array([[0, 0]]),
        position=np.array((0, 0, 1)),
        orientation=quaternion.from_rotation_matrix(dcm),
        focal_distance=1.0,
        sensor_width=0.1,
        sensor_height=0.1,
    )
    assert np.allclose(0, rays_1 - rays_2)


# Commented out temporarily since there was some problem in the test definition
# def test_camera_pointing_up_right():
#     """Test that a camera pointing up and to the right has a central ray
#     pointing in the same direction.
#     """
#     dcm = np.array([[1, 0, -1], [0, 1, 0], [1, 0, 1]])
#     dcm = dcm / np.linalg.norm(dcm, axis=1)

#     rays = geometry.get_sensor_rays(
#         sensor_coords=np.array([[0, 0]]),
#         position=np.array((0, 0, 0)),
#         orientation=quaternion.from_rotation_matrix(dcm),
#         focal_distance=1.0,
#         sensor_width=0.1,
#         sensor_height=0.1,
#     )
#     sqrt2 = np.sqrt(2)
#     assert np.allclose(rays[0], (1 / sqrt2, 0, 1 / sqrt2))


# Commented out temporarily since there was some problem in the test definition
# def test_ray_from_edge_of_sensor_should_point_horizontally():
#     """This is true if the camera is rotated 45 degrees and the total field of view
#     is 90 degrees.
#     """
#     dcm = np.array([[1, 0, -1], [0, 1, 0], [1, 0, 1]])
#     dcm = dcm / np.linalg.norm(dcm, axis=1)

#     rays = geometry.get_sensor_rays(
#         sensor_coords=np.array([[0.5, 0]]),
#         position=np.array((0, 0, 0)),
#         orientation=quaternion.from_rotation_matrix(dcm),
#         # A 2:1 ratio of width:focal distance gives 90 degree FOV
#         focal_distance=1.0,
#         sensor_width=2,
#         sensor_height=2,
#     )
#     rays = rays / np.linalg.norm(rays)
#     assert np.allclose(rays[0], np.array((0, 0, 1)))
