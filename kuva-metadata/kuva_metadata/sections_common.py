import typing
from datetime import datetime
from pathlib import Path
from typing import cast
from zoneinfo import ZoneInfo

from pint import Quantity, UnitRegistry
from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
)
from rasterio.rpc import RPC

from kuva_metadata.serializers import serialize_RPCs
from kuva_metadata.validators import check_is_utc_datetime, parse_rpcs, parse_date

_T = typing.TypeVar("_T")


class Header(BaseModel):
    """Header for the metadata files

    Attributes
    ----------
    version
        Version of the library used to create the file.
    author
        The author of the file.
    creation_date
        Creation date for the metadata file.
    """

    version: str
    author: str
    creation_date: datetime = datetime.now().astimezone(ZoneInfo("Etc/UTC"))

    _parse_timestamp = field_validator("creation_date", mode="before")(parse_date)
    _check_tz = field_validator("creation_date")(check_is_utc_datetime)
    model_config = ConfigDict(validate_assignment=True)


class Satellite(BaseModel):
    """Specifies the information relating to the satellite from which the file images
    where acquired.

    Attributes
    ----------
    name
        Short name of the satellite.
    cospar_id
        International designator assigned to the satellite after launch.
    launch_date
        When the satellite was launched
    """

    name: str
    cospar_id: str
    launch_date: datetime

    _parse_timestamp = field_validator("launch_date", mode="before")(parse_date)
    _check_tz = field_validator("launch_date")(check_is_utc_datetime)
    model_config = ConfigDict(validate_assignment=True)


class Radiometry(BaseModel):
    """Information required for TOA calculations and physical units

    Attributes
    ----------
    lut_file
        A lookup table stored together with the image file that associates raw image
        values to a radiance for different wavelengths and integration times. Stored as
        a numpy `npy` file.
    sun_spectrum_file
        Sun spectrum radiance of each band. Required for top of atmosphere calculation.
    """

    lut_file: Path
    sun_spectrum_file: Path


class RPCoefficients(BaseModel):
    """Rational polynomial function coefficients for orthorectification.

    A rational polynomial functions is simply a function which is the ratio of two
    polynomials. In our case we have two functions that are R^3 -> R^2 and map world
    coordinates to pixel space. The first function maps the x coordinates and the
    second the y coordinates.

    Attributes
    ----------
    rpcs
        Rational polynomial function coefficients for orthorectification
    """

    rpcs: RPC

    _parse_rpcs = field_validator("rpcs", mode="before")(parse_rpcs)

    @field_serializer("rpcs")
    def _serialize_RPCs(self, rpcs: RPC):
        return serialize_RPCs(rpcs)

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)


class BaseModelWithUnits(BaseModel, typing.Generic[_T]):
    """Allows an pint unit registry to be plugged in one of the classes using units"""

    @classmethod
    def model_validate_json_with_ureg(
        cls, json_data: str, new_ureg: UnitRegistry, **val_kwargs
    ) -> _T:
        """Will create a model from JSON data. However, the data will be copied so that
        each Quantity in all submodels is recursively converted to a new given
        UnitRegistry. If data is read from a JSON file without this method, it will be
        attached to the kuva-metadata default UnitRegistry.

        Parameters
        ----------
        json_data
            Model data to validate
        new_ureg
            Pint UnitRegistry to swap to

        Returns
        -------
            The validated model instance
        """
        model_instance = cls.model_validate_json(json_data, **val_kwargs)
        swapped_instance = cast(
            _T, swap_ureg_in_instance(model_instance, new_ureg, **val_kwargs)
        )

        return swapped_instance


class MetadataBase(BaseModelWithUnits):
    """Base class for all product levels' metadata

    Attributes
    ----------
    id
        Metadata ID for identifying metadata from DB
    header
        Metadata file header
    satellite
        Satellite the metadata's product has been created for
    image
        Image that the metadata is associated to
    """

    id: UUID4
    header: Header
    satellite: Satellite


def swap_ureg_in_instance(obj: BaseModel, new_ureg: UnitRegistry, **val_kwargs):
    """Swaps Pint UnitRegistry recursively within a pydantic model.

    Parameters
    ----------
    obj
        Instance of a model
    new_ureg
        Pint UnitRegistry to swap to
    val_kwargs
        Keyword arguments that are required in model validation, e.g. a pydantic context

    Returns
    -------
        The validated model instance which now has the new UnitRegistry in its or its
        child objects' Quantities
    """

    def _replace_ureg(value):
        """Helper recursion function to correctly go through the different attributes"""
        if isinstance(value, Quantity):
            return new_ureg.Quantity(value.magnitude, value.units)
        elif isinstance(value, BaseModel):
            return swap_ureg_in_instance(value, new_ureg, **val_kwargs)
        elif isinstance(value, (list, tuple, set)):
            return type(value)(_replace_ureg(v) for v in value)
        elif isinstance(value, dict):
            return {k: _replace_ureg(v) for k, v in value.items()}
        else:
            return value

    field_values = obj.model_dump(**val_kwargs)
    updated_field_values = _replace_ureg(field_values)
    return obj.__class__.model_validate(updated_field_values, **val_kwargs)
