import numpy as np

from kuva_geometry.ellipsoid import geodetic_to_xyz, xyz_to_geodetic


def test_geoid_to_ecef_roundtrip():
    """Test that geod to ECEF conversions work both ways"""

    lat, lon, h = np.deg2rad(28.0), np.deg2rad(-17.0), 737.0
    to_xyz = geodetic_to_xyz(lat, lon, h)
    back_to_geo = xyz_to_geodetic(*to_xyz)
    error = np.abs(np.array(back_to_geo) - np.array((28, -17, 737)))
    assert np.all(error < 1e-3)
