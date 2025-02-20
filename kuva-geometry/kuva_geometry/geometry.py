import numpy as np
import quaternion
from pint import Quantity


def plane_ray_intersection(
    ray: np.ndarray,
    position: np.ndarray,
    plane_normal: np.ndarray | None = None,
    p0: np.ndarray | None = None,
) -> np.ndarray:
    """
    Parameters
    ----------
    ray
        A rank 2 array with one ray per row. All rays must have a common point given
        by `position`
    position
        A point through which all the rays go through
    plane_normal
        Normal to the plane we want to intersect
    p0
        A point on the plane we want to intersect
    """
    ray = np.atleast_2d(ray)

    if plane_normal is None:
        plane_normal = np.array([0, 0, 1])

    if p0 is None:
        p0 = np.array([0, 0, 0])

    # This matrix product reduces to the dot product of ray and normal when there
    # is only one ray.
    denominator = ray @ plane_normal
    t = -np.dot(plane_normal, position - p0) / denominator

    intersection = position + t[:, None] * ray
    return intersection.squeeze()


def sphere_ray_intersection(
    rays: np.ndarray,
    rays_origin: np.ndarray,
    sphere_center: np.ndarray,
    sphere_radius: float,
    normalize_rays: bool = True,
) -> np.ndarray:
    """
    Return the closest intersection of the ray with the sphere.

    Notes
    -----
    - Assumption: Ray origin is outside of the sphere
    - Assumption: Ray direction is pointing towards the sphere

    Parameters
    ----------
    rays
        Rank 2 array of dimensions (n_rays, 3) with the cartesian components
        of the direction vectors. Normalization will happen internally unless
        it is disabled.
    rays_origin
        Rank 1 array with the origin for all the rays
    sphere_center
        Rank 1 array with the position of the sphere center
    sphere_radius
        Radius of the sphere
    normalize_rays
        The ray sphere intersection implemented requires the ray direction to
        be normalized. The default is to normalize internally but you can
        save cycles if you promise they are already normalized by setting
        this parameter to `False`.
    """
    # Validate parameters
    if rays.ndim != 2:
        e_ = "The rays array should have rank 2"
        raise ValueError(e_)

    if rays.shape[1] != 3:
        e_ = "The second dimension of the rays array should be 3"
        raise ValueError(e_)

    if rays_origin.ndim != 1 or len(rays_origin) != 3:
        e_ = "Rays origin should be a 1d array of length 3"
        raise ValueError(e_)

    # Make sure rays are normalized
    if normalize_rays:
        # The transpose dance makes broadcasting work
        rays = (rays.T / np.sqrt((rays**2).sum(axis=1))).T

    # Calculate intersections
    r0 = rays_origin - sphere_center
    ray_dot_r0 = np.dot(rays, r0)
    t = -ray_dot_r0 - np.sqrt(
        ray_dot_r0**2 - np.dot(r0, r0) + sphere_radius * sphere_radius
    )

    intersection = t[:, np.newaxis] * rays + r0

    return intersection


def find_aligning_quaternion(
    Q: quaternion.quaternion, u: np.ndarray, v: np.ndarray
) -> quaternion.quaternion:
    """Find the shortest quaternion that aligns two vectors.

    Parameters
    ----------
    Q
        Quaternion describing the initial orientation
    u
        3-element indexable describing the starting vector
    v
        3-element indexable describing the ending vector
    """
    U = quaternion.quaternion(0, u[0], u[1], u[2])
    V = quaternion.quaternion(0, v[0], v[1], v[2])

    return ((U * V).absolute() * Q - V * Q * U).normalized()


def get_sensor_rays(
    sensor_coords: np.ndarray,
    position: np.ndarray,
    orientation: quaternion.quaternion,
    focal_distance: Quantity,
    sensor_width: Quantity,
    sensor_height: Quantity,
    use_negative_sensor_plane: bool = False,
) -> np.ndarray:
    r"""
    Calculate the vectors that join the back nodal point to the sensor corners.

    Parameters
    ----------
    sensor_coords
        Rank 2 array of dimensions (n_rays, 2) with (u, v) coordinates of each ray.
    position
        3 element indexable with the position of back nodal point in cartesian coords.
    orientation: quaternion.quaternion
        Quaternion describing the orientation of the camera
    sensor_width: float
        Width of the sensor must be in the same units as `position`
    sensor_height: float
        Height of the sensor must be in the same units as `position`
    use_negative_sensor_plane
        Whether to use the negative sensor plane to calculate the corner rays.
        Use when you are dealing with a truly raw image from a sensor which is
        physically inverted due to passing through the camera center before
        hitting the sensor. See below for more explanations.

    Notes
    -----
    - `focal_distance`, `sensor_width` and `sensor_height` MUST be given in the same
      units.

    Negative VS Positive sensor plane
    ---------------------------------
    On a pinhole camera model (as appropriate for many real cameras) the image
    on the sensor comes out inverted. For this reason people will usually
    define a positive plane placed on front of the camera sensor where the
    image is not inverted. The name positive and negative come from the olden
    time when we had camera rolls that recorded a negative of the image.

    If you are dealing with raw images from a sensor you need to draw the
    camera rays from the actual physical place where the happen i.e. the
    sensor/negative. If this is not done then the corners of the sensors will
    be mapped to the wrong places on the ground. Why this inversion happens can
    be visualized by looking at the following pinhole camera diagram:

               d'
                ──────────────────── a'
               /\                '/
              /  \             ' /   negative
             /   \            ' /
            /     \          ' /
           /       \        ' /
        c' ────────────── ───/
            `        \     '  b'
             ``      \    '
               ``     \  '
                 ``  \  '               b->b' ray not shown
                   `` \'                      for clarity
                    ``\  camera center
                     ' \`
                     ' \ `v             `v` indicates direction of rays
                    '   \  ``
                   v    v     ``
              b   '      \      ``
                ─' ──────\ ───────`/ c
               /'         \       /
              /'          \      /
             /'            \    /
            /'             \   /
           /'               \ /
           ──────────────────/  positive
          a                   d

    The ground is down and camera rays go from the negative through the camera
    center and keep on going until they hit the ground.
    """
    # NOTE: Position is irrelevant as demonstrated by the test and under
    # `test_sensor_rays`. But I like it in the equations below because it makes
    # things clearer physically speaking.

    # Construct camera sensor basis by rotating the ECEF coordinate reference system
    # using the conjugate/inverted orientation. The conjugate is required because
    # the `orientation` takes us from the image sensor to the ECEF crs. The conjugate
    # takes us from the ECEF crs to the image sensor, which is what we need.
    camera_frame = np.identity(3)  # ECEF (cartesian) crs
    camera_frame = quaternion.rotate_vectors(
        orientation.conjugate(), camera_frame, axis=0
    )

    # NOTE: these are row vectors.
    u_ = camera_frame[0, :] * sensor_width  # x-axis
    v_ = camera_frame[1, :] * sensor_height  # y-axis
    w = camera_frame[2, :]  # z-axis

    # If we need to use the negative sensor plane then the images are inverted, i.e.
    # there is a switch of signs on the rows and columns. This sign will be used
    # to keep track of it.
    sign = -1 if use_negative_sensor_plane else 1

    # if `use_negative_plane == True` then the image sensor center is behind the camera
    # center instead of in front.
    # INFO: We call sensor to whatever plane we are using. If that's the positive please
    # do remember that in physical reality there is no sensor there.
    image_sensor_center = position + w * sign * focal_distance

    # x, y go from -0.5, to 0.5 with 0 being the center of the camera and
    # (-0.5, 0.5) the top left corner as viewed from the back nodal point
    # (0.5, -0.5) the bottom right corner as viewed from the BNP.

    def in_frame_coord(uv_coords):
        x, y = uv_coords[:, 0], uv_coords[:, 1]
        return image_sensor_center - x[:, None] * u_ - y[:, None] * v_

    # The sign below is to make sure that the rays are pointing toward the ground.
    # In the positive case (sign=+1) we go from the ray origin (aka camera center)
    # towards the corners of the sensor. In the negative (sign=-1) we go from the
    # corners of the sensor towards the camera center.
    return sign * (in_frame_coord(sensor_coords) - position)


def get_sensor_corner_rays(
    position: np.ndarray,
    orientation: quaternion.quaternion,
    focal_distance: Quantity,
    sensor_width: Quantity,
    sensor_height: Quantity,
    use_negative_sensor_plane: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculate the vectors that join the back nodal point to the sensor corners.

    Parameters
    ----------
    position
        3 element indexable with the position of back nodal point in cartesian coords.
    orientation: quaternion.quaternion
        Quaternion describing the orientation of the camera
    sensor_width: float
        Width of the sensor must be in the same units as `position`
    sensor_height: float
        Height of the sensor must be in the same units as `position`
    use_negative_sensor_plane
        Whether to use the negative sensor plane to calculate the rays.
    """
    top_left_corner = [-0.5, 0.5]
    top_right_corner = [0.5, 0.5]
    bottom_right_corner = [0.5, -0.5]
    bottom_left_corner = [-0.5, -0.5]

    sensor_corners = np.vstack(
        [top_left_corner, top_right_corner, bottom_right_corner, bottom_left_corner]
    )

    return position, get_sensor_rays(
        sensor_corners,
        position,
        orientation,
        focal_distance,
        sensor_width,
        sensor_height,
        use_negative_sensor_plane,
    )
