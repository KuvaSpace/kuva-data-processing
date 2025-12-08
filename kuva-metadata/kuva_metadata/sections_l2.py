"""Metadata specification for L2 products"""

from pydantic import ConfigDict

# Unused imports are kept so that common objects are available with one import
from kuva_metadata.sections_common import (  # noqa # pylint: disable=unused-import
    Header,
    MetadataBase,
    Radiometry,
    RPCoefficients,
    Satellite,
)
from kuva_metadata.sections_l1 import (  # noqa # pylint: disable=unused-import
    Band,
    Image,
)


class BandL2A(Band):
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
    viewing_zenith_angle
        The viewing zenith angle of the central pixel of the band.
    viewing_azimuth_angle
        The viewing azimuth angle of the central pixel of the band.
    """

    pass


class ImageL2A(Image):
    bands: list[BandL2A]


class MetadataLevel2A(MetadataBase):
    """Metadata for Level-2A products

    Attributes
    ----------
    MetadataBase attributes
        All attributes included in parent MetadataBase
    rpcs
        Rational polynomial function coefficients for product orthorectification
    """

    image: ImageL2A

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
