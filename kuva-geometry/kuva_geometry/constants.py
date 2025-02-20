"""Some useful constants."""

# NOTE: We don't use pint here because it's not used evenly enough across the
# codebase. If you end up using them it is recommended you attach units to them
# immediately.

# Source: https://github.com/geospace-code/pymap3d/blob/main/src/pymap3d/ellipsoid.py
EARTH_SEMIMAJOR_AXIS = 6378137.0  # WGS84 Earth semimajor axis (meters)
EARTH_SEMIMINOR_AXIS = 6356752.31424518  # WGS84 Earth semiminor axis (meters)
