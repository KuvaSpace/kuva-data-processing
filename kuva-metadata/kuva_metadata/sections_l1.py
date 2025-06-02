"""Metadata specification for L1 products"""

from datetime import datetime

from pint import Quantity
from pydantic import UUID4, ConfigDict, field_serializer, field_validator

# Unused imports are kept so that common objects are available with one import
from kuva_metadata.sections_common import (  # noqa # pylint: disable=unused-import
    BaseModelWithUnits,
    Header,
    MetadataBase,
    Radiometry,
    RPCoefficients,
    Satellite,
)

from .serializers import serialize_quantity
from .validators import (
    check_is_utc_datetime,
    must_be_angle,
    must_be_positive_distance,
    parse_date,
)


class Band(BaseModelWithUnits):
    """Band metadata.

    Attributes
    ----------
    index
        Index within a datacube associated with the band (0-indexed).
    wavelength
        Nominal wavelength associated with the Fabry-Perot Interferometer position.
    """

    index: int
    wavelength: Quantity

    _check_wl_distance = field_validator("wavelength", mode="before")(
        must_be_positive_distance
    )
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    @field_serializer("wavelength", when_used="json")
    def _serialize_quantity(self, q: Quantity):
        return serialize_quantity(q)


class Image(BaseModelWithUnits):
    """Hyperspectral image metadata containing bands

    Attributes
    ----------
    bands
        _description_
    local_solar_zenith_angle
        Solar zenith angle of the image area
    local_solar_azimuth_angle
        Solar azimuth angle of the image area
    local_viewing_angle
        The angle between the satellite's pointing direction and nadir.
    acquired_on
        Time of image acquisition
    source_images
        List of database IDs of images this L1 product image has been stitched from
    measured_quantity_name
        Name of pixel value unit
    measured_quantity_unit
        Unit of pixel values
    cloud_cover_percentage
        The cloud cover percentage
    """

    bands: list[Band]
    local_solar_zenith_angle: Quantity
    local_solar_azimuth_angle: Quantity
    local_viewing_angle: Quantity
    acquired_on: datetime
    source_images: list[UUID4]
    measured_quantity_name: str
    measured_quantity_unit: str
    cloud_cover_percentage: float | None

    _check_angle = field_validator(
        "local_solar_zenith_angle",
        "local_solar_azimuth_angle",
        "local_viewing_angle",
        mode="before",
    )(must_be_angle)
    _parse_timestamp = field_validator("acquired_on", mode="before")(parse_date)
    _check_tz = field_validator("acquired_on")(check_is_utc_datetime)
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    @field_serializer(
        "local_solar_zenith_angle",
        "local_solar_azimuth_angle",
        "local_viewing_angle",
        when_used="json",
    )
    def _serialize_quantity(self, q: Quantity):
        return serialize_quantity(q)


class MetadataLevel1AB(MetadataBase):
    """Metadata for Level-1A and Level-1B products

    Attributes
    ----------
    MetadataBase attributes
        All attributes included in parent MetadataBase
    """

    image: Image

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)


class MetadataLevel1C(MetadataBase):
    """Metadata for Level-1C products

    Attributes
    ----------
    MetadataBase attributes
        All attributes included in parent MetadataBase
    rpcs
        Rational polynomial function coefficients for product orthorectification
    """

    image: Image
    rpcs: RPCoefficients | None

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
