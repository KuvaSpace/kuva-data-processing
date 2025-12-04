"""Metadata specification for L1 products"""

from pydantic import ConfigDict

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


class BandL1AB(Band):
    """Band metadata.

    Attributes
    ----------
    index
        Index within a datacube associated with the band (0-indexed).
    wavelength
        Nominal wavelength associated with the Fabry-Perot Interferometer position.
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
    """

    toa_radiance_to_reflectance_factor: float = 1.0


class BandL1C(Band):
    """Band metadata.

    Attributes
    ----------
    index
        Index within a datacube associated with the band (0-indexed).
    wavelength
        Nominal wavelength associated with the Fabry-Perot Interferometer position.
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


class MetadataLevel1C(MetadataBase):
    """Metadata for Level-1C products

    Attributes
    ----------
    MetadataBase attributes
        All attributes included in parent MetadataBase
    """

    image: ImageL1C
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
