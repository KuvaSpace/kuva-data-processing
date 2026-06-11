"""Metadata specification for L1 products"""

from pydantic import BaseModel, ConfigDict, Field

# Unused imports are kept so that common objects are available with one import
from kuva_metadata.sections_common import (  # noqa # pylint: disable=unused-import
    Band,
    Header,
    Image,
    MetadataBase,
    Radiometry,
    RPCoefficients,
    Satellite,
)

DEFAULT_REFERENCE_BASEMAP_SOURCE = "esri_world_imagery"
DEFAULT_REFERENCE_BASEMAP_URI = (
    "https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9"
)
DEFAULT_REFERENCE_DEM_URI = "https://doi.org/10.5270/ESA-c5d3d65"
DEM_REFERENCE_SOURCE_MAP = {
    "glo_30": "COP-DEM_GLO-30-DGED",
    "glo_90": "COP-DEM_GLO-90-DGED",
    "srtm_1": "SRTM1",
}


class BandL1AB(Band):
    """Band metadata.

    Attributes
    ----------
    index
        Index within a datacube associated with the band (0-indexed).
    wavelength
        The barycenter wavelength associated with the acquired band.
    scale
        Scale to convert stored pixel values to radiance.
    offset
        Offset to convert stored pixel values to radiance.
    toa_radiance_to_reflectance_factor
        Factor to convert from top-of-atmosphere radiance to reflectance.
        Example: reflectance = radiance * toa_radiance_to_reflectance_factor
    viewing_zenith_angle
        The viewing zenith angle of the central pixel of the band.
    viewing_azimuth_angle
        The viewing azimuth angle of the central pixel of the band.
    camera_name
        Name of the camera that acquired the band.
    """

    toa_radiance_to_reflectance_factor: float = 1.0


class BandL1C(Band):
    """Band metadata.

    Attributes
    ----------
    index
        Index within a datacube associated with the band (0-indexed).
    wavelength
        The barycenter wavelength associated with the acquired band.
    scale
        Scale to convert stored pixel values to radiance.
    offset
        Offset to convert stored pixel values to radiance.
    toa_radiance_to_reflectance_factor
        Factor to convert from top-of-atmosphere radiance to reflectance.
        Example: reflectance = radiance * toa_radiance_to_reflectance_factor
    viewing_zenith_angle
        The viewing zenith angle of the central pixel of the band.
    viewing_azimuth_angle
        The viewing azimuth angle of the central pixel of the band.
    camera_name
        Name of the camera that acquired the band.
    """

    toa_radiance_to_reflectance_factor: float = 1.0


class ImageL1AB(Image):
    bands: list[BandL1AB]


class ImageL1C(Image):
    bands: list[BandL1C]


class MetadataLevel1AB(MetadataBase):
    """Metadata for Level-1A and Level-1B products

    Attributes
    ----------
    MetadataBase attributes
        All attributes included in parent MetadataBase
    """

    image: ImageL1AB
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)


class GeolocationReference(BaseModel):
    """Reference dataset or telemetry used by a geolocation step."""

    source: str
    type: str | None = Field(default=None, exclude_if=lambda value: value is None)
    uri: str | None = Field(default=None, exclude_if=lambda value: value is None)

    model_config = ConfigDict(validate_assignment=True)


class GeoreferencingProcess(BaseModel):
    """Georeferencing step provenance for L1C products."""

    method: str
    reference: GeolocationReference

    model_config = ConfigDict(validate_assignment=True)


class OrthorectificationProcess(BaseModel):
    """Orthorectification step provenance for L1C products."""

    method: str
    reference: GeolocationReference

    model_config = ConfigDict(validate_assignment=True)


class GeolocationProcessConfiguration(BaseModel):
    """Configuration details for the geolocation process."""

    georeferencing: GeoreferencingProcess
    orthorectification: OrthorectificationProcess

    model_config = ConfigDict(validate_assignment=True)


class GeolocationProcess(BaseModel):
    """Geolocation process provenance for L1C products."""

    method: str
    configuration: GeolocationProcessConfiguration
    fallback_reason: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )

    model_config = ConfigDict(validate_assignment=True)


class MetadataLevel1C(MetadataBase):
    """Metadata for Level-1C products

    Attributes
    ----------
    MetadataBase attributes
        All attributes included in parent MetadataBase
    """

    image: ImageL1C
    geolocation_process: GeolocationProcess | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
