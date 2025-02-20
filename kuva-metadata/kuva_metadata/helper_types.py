"""Additional type aliases"""

import numpy as np
from pint import Quantity
from quaternion import quaternion
from shapely import Polygon

# All this types with lists would be better expressed with tuples but pydantic
# reads the json as lists so we have a type to match.
Quantity_ = Quantity | list[float | str]
quaternion_ = quaternion | list[float]
array_3x3_ = np.ndarray | list[list[float]]
Polygon_ = Polygon | str
