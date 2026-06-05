"""Metadata specification for L2 products"""

from pydantic import ConfigDict

# Unused imports are kept so that common objects are available with one import
from kuva_metadata.sections_common import (  # noqa # pylint: disable=unused-import
    AtmosphericCorrectionConfiguration,
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
        The barycenter wavelength associated with the acquired band.
    scale
        Scale to convert stored pixel values to radiance.
    offset
        Offset to convert stored pixel values to radiance.
    viewing_zenith_angle
        The viewing zenith angle of the central pixel of the band.
    viewing_azimuth_angle
        The viewing azimuth angle of the central pixel of the band.
    camera_name
        Name of the camera that acquired the band.
    """

    pass


class ImageL2A(Image):
    """Hyperspectral L2A image metadata containing bands

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
    footprint
        Shapely polygon describing an estimated footprint of the satellite
    epsg
        EPSG code of the image coordinate reference system
    shape
        Shape of the image (height, width)
    gsd
        Ground sample distance (height, width or row, col) using projection unit in
        CRS `epsg`.
    transform
        Affine transformation mapping pixel coordinates to coordinates in the CRS
        `epsg`.
    """

    bands: list[BandL2A]


class AtCorConfigL2A(AtmosphericCorrectionConfiguration):
    """Atmospheric correction configuration for L2A

    Attributes
    ----------
    method
        Method used for atmospheric correction
    atmospheric_state
        Atmospheric state variables
    geometry_state
        Geometry state variables
    scene_state
        Scene state variables
    """

    pass


class MetadataLevel2A(MetadataBase):
    """Metadata for Level-2A products

    Attributes
    ----------
    MetadataBase attributes
        All attributes included in parent MetadataBase
    """

    image: ImageL2A
    atmospheric_correction_configuration: AtCorConfigL2A | None = None

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
