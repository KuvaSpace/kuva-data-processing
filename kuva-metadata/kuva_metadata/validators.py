"""Validators for non-standard classes.

This let know Pydantic how to take of types such as shapely.geometry or quaternions
"""

from datetime import datetime
from typing import cast
from zoneinfo import ZoneInfo

import numpy as np
import shapely
from pint import Quantity
from quaternion import quaternion
from rasterio.crs import CRS
from rasterio.rpc import RPC
from shapely import Polygon, from_wkt

from .custom_types import CRSGeometry
from .helper_types import Polygon_, Quantity_, array_3x3_, quaternion_
from .utils import default_ureg


def parse_crs_geometry(geom: CRSGeometry | dict[str, str | int]) -> CRSGeometry:
    """Parses shapely geometries with an associated CRS"""
    if isinstance(geom, dict):
        crs_geometry = CRSGeometry(
            geom=from_wkt(geom["geom"]), crs_epsg=CRS.from_epsg(geom["crs_epsg"])
        )
    elif isinstance(geom, CRSGeometry):
        crs_geometry = geom
    else:
        msg = (
            "Only list of the form [wkt_string, epsg_int] can be interpreted as "
            "CRSGeometry"
        )
        raise ValueError(msg)

    return crs_geometry


def parse_date(date: datetime | str) -> datetime:
    """Parses dates and makes sure they are UTC"""
    if isinstance(date, str):
        date = datetime.fromisoformat(date.replace("Z", "+00:00"))

    return date


def parse_rpcs(rpcs: RPC | dict[str, float | np.ndarray]) -> RPC:
    """Parses the RPCs and makes sure they are RPC objects"""
    if isinstance(rpcs, dict):
        rpcs = RPC(**rpcs)
    else:
        msg = "Only dicts can be coerced into RPC objects."
        raise ValueError(msg)
    return rpcs


def parse_quaternion(q: quaternion_) -> quaternion:
    """Parse 4 values into a numpy-quaternion"""
    if isinstance(q, list):
        try:
            q = quaternion(*q)
        except Exception:
            msg = "Input list couldn't be interpreted as quaternion"
            raise ValueError(msg)
    elif isinstance(q, quaternion):
        q = q
    else:
        msg = "Only lists can be coerced into quaternions."
        raise ValueError(msg)

    return q


def parse_3x3_matrix(arr: array_3x3_) -> np.ndarray | None:
    """Parse list of lists into 3x3 numpy array"""
    if arr is None:
        return None

    if isinstance(arr, list):
        arr = np.array(arr)
    elif isinstance(arr, np.ndarray):
        arr = arr
    else:
        msg = "Only list[list[float]] can be coereced into matrices."
        raise ValueError(msg)

    if not arr.shape == (3, 3):
        msg = f"Only 3x3 matrices should be accepted, got {arr.shape}"
        raise ValueError(msg)

    return arr


def parse_polygon(poly: Polygon_) -> Polygon:
    """Parse a shapely polygon from a WKT string"""
    if isinstance(poly, str):
        poly = shapely.from_wkt(poly)
    elif isinstance(poly, Polygon):
        poly = poly
    else:
        msg = "Only strings can be reinterpreted as polygons"
        raise ValueError(msg)

    return poly


def parse_quantity(quantity: Quantity_) -> Quantity:
    """Parse a Pint quantity from a tuple (value, unit)"""
    if isinstance(quantity, list):
        if not isinstance(quant := quantity[0], float):
            raise ValueError
        if not isinstance(unit := quantity[1], str):
            raise ValueError

        quantity_ = cast(Quantity, Quantity(quant, default_ureg.Unit(unit)))
    elif isinstance(quantity, Quantity):
        quantity_ = cast(Quantity, quantity)
    else:
        msg = (
            "Only a list of the form [value, unit] can be reinterpreted back as"
            " quantity."
        )
        raise ValueError(msg)

    return quantity_


def must_be_unit(quantity: Quantity_, unit: str) -> Quantity:
    """Parse a Pint quantity while making sure it is compatible with a specific unit"""
    quantity = parse_quantity(quantity)
    if not quantity.is_compatible_with(unit):
        raise ValueError(f"Quantity should be compatible with {unit}")

    return quantity


def must_be_distance(quantity: Quantity_) -> Quantity:
    """Parse a Pint unit and make sure it has units of distance"""
    return must_be_unit(quantity, "meter")


def must_be_time(quantity: Quantity_) -> Quantity:
    """Parse a Pint unit and make sure it has units of time"""
    return must_be_unit(quantity, "second")


def must_be_angle(quantity: Quantity_) -> Quantity:
    """Parse a Pint unit and make sure it has units of angle"""
    return must_be_unit(quantity, "degree")


def must_be_speed(quantity: Quantity_) -> Quantity:
    """Parse a Pint unit and make sure it has units of speed"""
    return must_be_unit(quantity, "meter_per_second")


def must_be_temperature(quantity: Quantity_) -> Quantity:
    """Parse a Pint unit and make sure it has units of temperature"""
    return must_be_unit(quantity, "K")


def must_be_pressure(quantity: Quantity_) -> Quantity:
    """Parse a Pint unit and make sure it has units of pressure"""
    return must_be_unit(quantity, "Pa")


def must_be_positive_quantity(quantity: Quantity_) -> Quantity:
    """Parse a Pint unit and make sure its positive"""
    quantity = parse_quantity(quantity)
    if quantity <= 0:
        msg = "Should be positive"
        raise ValueError(msg)
    return quantity


def must_be_positive_distance(quantity: Quantity_) -> Quantity:
    """Parse a Pint object and make sure it a positive distance"""
    quantity = parse_quantity(quantity)
    quantity = must_be_positive_quantity(quantity)
    quantity = must_be_distance(quantity)

    return quantity


def must_be_positive_time(quantity: Quantity_) -> Quantity:
    """Parse a Pint object and make sure it a positive time"""
    quantity = parse_quantity(quantity)
    quantity = must_be_positive_quantity(quantity)
    quantity = must_be_time(quantity)

    return quantity


def check_is_utc_datetime(timestamp: datetime) -> datetime:
    """Parse a timestamp and make sure it's UTC"""
    if timestamp.tzname() != "UTC":
        msg = "Only UTC datetimes are allowed."
        raise ValueError(msg)

    return timestamp
