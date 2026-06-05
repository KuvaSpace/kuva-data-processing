import typing
from datetime import datetime
from typing import Annotated, cast
from zoneinfo import ZoneInfo

from pint import Quantity, UnitRegistry
from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
    SerializationInfo,
    field_serializer,
    field_validator,
)
from rasterio import Affine
from rasterio.rpc import RPC

from kuva_metadata.custom_types import CRSGeometry
from kuva_metadata.serializers import (
    serialize_camera_radiometric_ids,
    serialize_CRSGeometry,
    serialize_quantity,
    serialize_rio_metadata,
    serialize_RPCs,
)
from kuva_metadata.validators import (
    check_is_utc_datetime,
    must_be_angle,
    must_be_distance,
    must_be_mixing_ratio_or_none,
    must_be_positive_distance,
    must_be_positive_float,
    must_be_positive_quantity,
    must_be_pressure,
    must_be_speed,
    must_be_valid_aerosol_type,
    must_be_valid_atmospheric_season,
    parse_camera_radiometric_ids,
    parse_crs_geometry,
    parse_date,
    parse_rpcs,
)

_T = typing.TypeVar("_T")


class Header(BaseModel):
    """Header for the metadata files

    Attributes
    ----------
    version
        Version (commit hash) of the library used to create the product.
    tag
        Baseline tag indicating with which baseline version the product was created.
    author
        The author of the file.
    creation_date
        Creation date for the metadata file.
    """

    version: str
    tag: str | None = Field(default=None, exclude_if=lambda v: v is None)
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
    """Radiometric model per camera used to create the product.

    Attributes
    ----------
    camera_radiometric_ids
        A mapping of camera names to their respective radiometric model IDs.
    """

    camera_radiometric_ids: dict[str, UUID4]

    _parse_camera_radiometric_ids = field_validator(
        "camera_radiometric_ids", mode="before"
    )(parse_camera_radiometric_ids)

    @field_serializer("camera_radiometric_ids")
    def _serialize_camera_radiometric_ids(
        self, camera_radiometric_ids: dict[str, UUID4]
    ) -> dict[str, str]:
        return serialize_camera_radiometric_ids(camera_radiometric_ids)


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
    radiometric_model
        Radiometric model used to create the product. Defaults to None for backwards
        compatibility, but should be always set, if possible.
    satellite
        Satellite the metadata's product has been created for
    image
        Image that the metadata is associated to
    """

    id: UUID4
    header: Header
    radiometric_model: Radiometry | None = None
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


class Band(BaseModelWithUnits):
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

    index: int
    wavelength: Quantity
    viewing_zenith_angle: Quantity | None = Field(default=None)
    viewing_azimuth_angle: Quantity | None = Field(default=None)
    camera_name: str | None = Field(default=None)

    scale: float = 1.0
    offset: float = 0.0

    _check_wl_distance = field_validator("wavelength", mode="before")(
        must_be_positive_distance
    )
    _check_viewing_zenith_angle = field_validator(
        "viewing_zenith_angle", mode="before"
    )(must_be_angle)
    _check_viewing_azimuth_angle = field_validator(
        "viewing_azimuth_angle", mode="before"
    )(must_be_angle)

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    @field_serializer("wavelength", when_used="json")
    def _serialize_quantity(self, q: Quantity | None):
        if q is None:
            return None
        return serialize_quantity(q)

    @field_serializer("viewing_zenith_angle", when_used="json")
    def _serialize_viewing_zenith_angle(self, q: Quantity | None):
        if q is None:
            return None
        return serialize_quantity(q)

    @field_serializer("viewing_azimuth_angle", when_used="json")
    def _serialize_viewing_azimuth_angle(self, q: Quantity | None):
        if q is None:
            return None
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
    altitude
        Altitude of the satellite relative to WGS84, i.e. the height above the WGS-84
        ellipsoid.
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

    local_solar_zenith_angle: Quantity
    local_solar_azimuth_angle: Quantity
    local_viewing_angle: Quantity
    altitude: Quantity | None = None
    acquired_on: datetime
    source_images: list[UUID4]
    measured_quantity_name: str
    measured_quantity_unit: str
    cloud_cover_percentage: float | None
    footprint: CRSGeometry | None = None
    epsg: int | None = None
    shape: tuple[int, int] | None = None  # (height, width)
    gsd: tuple[float, float] | None = None  # Ground sample distance
    transform: Affine | None = None

    _check_angle = field_validator(
        "local_solar_zenith_angle",
        "local_solar_azimuth_angle",
        "local_viewing_angle",
        mode="before",
    )(must_be_angle)
    _check_altitude = field_validator("altitude", mode="before")(
        must_be_positive_distance
    )
    _parse_timestamp = field_validator("acquired_on", mode="before")(parse_date)
    _check_tz = field_validator("acquired_on")(check_is_utc_datetime)
    _parse_geom = field_validator("footprint", mode="before")(parse_crs_geometry)

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    @field_serializer(
        "local_solar_zenith_angle",
        "local_solar_azimuth_angle",
        "local_viewing_angle",
        "altitude",
        when_used="json",
    )
    def _serialize_quantity(self, q: Quantity | None):
        if q is None:
            return None
        return serialize_quantity(q)

    @field_serializer("footprint")
    def _serialize_CRSGeometry(self, p: CRSGeometry | None):
        return serialize_CRSGeometry(p)

    @field_serializer("epsg")
    def _serialize_epsg(self, epsg: int | None, info: SerializationInfo) -> int:
        # Don't use the passed field because we get the epsg from the image
        return serialize_rio_metadata(info, "epsg")

    @field_serializer("shape")
    def _serialize_shape(
        self, shape: tuple[int, int] | None, info: SerializationInfo
    ) -> tuple[int, int] | None:
        # Don't use the passed field because we get the shape from the image
        return serialize_rio_metadata(info, "shape")

    @field_serializer("gsd")
    def _serialize_gsd(
        self, gsd: tuple[float, float] | None, info: SerializationInfo
    ) -> tuple[float, float] | None:
        # Don't use the passed field because we get the gsd from the image
        return (
            serialize_rio_metadata(info, "gsd_h"),
            serialize_rio_metadata(info, "gsd_w"),
        )

    @field_serializer("transform")
    def _serialize_geotransform(
        self, transform: Affine | None, info: SerializationInfo
    ) -> Affine | None:
        # Don't use the passed field because we get the transform from the image
        return serialize_rio_metadata(info, "transform")


class StateMetaBase(BaseModelWithUnits):
    """Base class for all state metadata

    Attributes
    ----------
    source
        String containing the source of the state variables
    """

    source: str


class AtmosphericStateVariables(BaseModelWithUnits):
    """Variables in the AtmosphericState

    Attributes:
    -----------
    tco3
        Total column of ozone [DU]
    tcwv
        Total column of water vapour [cm]
    aot550
        Aerosol optical thickness @ 550 nm
    tc_co2
        Total column of CO2 [ppm]
    mr_ch4
        Mixing ratio of methane [ppm]
    pressure
        Pressure [hPa]
    wind_speed
        Wind Speed [m/s]
    aerosol_type
        Aerosol type ('rural'/'maritime')
    atmospheric_season
        Atmospheric season ('midlatitude_summer'/'midlatitude_winter')
    """

    tco3: Quantity
    tcwv: Quantity
    aot550: float
    tc_co2: Quantity | None = Field(default=None)
    mr_ch4: Quantity | None = Field(default=None)
    pressure: Quantity
    wind_speed: Quantity
    aerosol_type: str  # coastal or maritime
    atmospheric_season: str | None = Field(default=None)  # Summer or winter

    _check_press = field_validator("pressure", mode="before")(must_be_pressure)
    _check_wind_speed = field_validator("wind_speed", mode="before")(must_be_speed)
    _check_aerosol = field_validator("aot550", mode="before")(must_be_positive_float)
    _check_aerosol_type = field_validator("aerosol_type", mode="before")(
        must_be_valid_aerosol_type
    )
    _check_tcwv = field_validator("tcwv", mode="before")(must_be_positive_distance)
    _check_ozone = field_validator("tco3", mode="before")(must_be_positive_quantity)
    _check_valid_atmos_seasons = field_validator("atmospheric_season", mode="before")(
        must_be_valid_atmospheric_season
    )
    _check_valid_mixing_ratio = field_validator("tc_co2", "mr_ch4", mode="before")(
        must_be_mixing_ratio_or_none
    )

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    @field_serializer(
        "tco3",
        "tcwv",
        "pressure",
        "wind_speed",
        when_used="json",
    )
    def _serialize_quantity(self, q: Quantity | None):
        return serialize_quantity(q)

    @field_serializer("tc_co2", "mr_ch4", when_used="json")
    def _serialize_maybe_none_quantity(self, q: Quantity | None):
        if q is None:
            return None
        return serialize_quantity(q)


class GeometryStateVariables(BaseModelWithUnits):
    """Variables in the GeometryState

    Attributes:
    -----------
    sza
        Sun zenith angle
    saa
        Sun azimuth angle
    vza
        View zenith angle
    vaa
        View azimuth angle
    altitude
        Altitude

    For sun and view azimuth angles, we are using Libradtran's viewing and sun azimuth
    angle conventions. That means:
    For vaa:
    - Sensor in the North (looking South): 0 deg
    - Sensor in the East (looking West): 90 deg
    - Sensor in the South (looking North): 180 deg
    - Sensor in the West (looking East): 270 deg
    For saa:
    - Sun in the South: 0 degrees
    - Sun in the West: 90 degrees
    - Sun in the North: 180 degrees
    - Sun in the East: 270 degrees

    The relative azimuth angle (raa) is computed as vaa-saa
    """

    sza: Quantity
    saa: Quantity | None = Field(default=None)
    vza: Quantity
    vaa: Quantity | None = Field(default=None)
    altitude: Quantity | None = Field(default=None)

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    _check_angle = field_validator(
        "sza",
        "saa",
        "vza",
        "vaa",
        mode="before",
    )(must_be_angle)

    _check_altitude = field_validator("altitude", mode="before")(must_be_distance)

    @field_serializer(
        "sza",
        "vza",
        when_used="json",
    )
    def _serialize_quantity(self, q: Quantity):
        return serialize_quantity(q)

    @field_serializer("saa", "vaa", "altitude", when_used="json")
    def _serialize_maybe_none_quantity(self, q: Quantity | None):
        if q is None:
            return None
        return serialize_quantity(q)


class SceneStateVariables(BaseModelWithUnits):
    """Variables in the SceneState

    Attributes:
    -----------
    land_percentage
        Percentage of land in the scene (float)"""

    land_percentage: Annotated[float, Field(gt=0, lt=100)] | None

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    _check_landperc = field_validator("land_percentage", mode="before")(
        must_be_positive_float
    )


class AtmosphericState(StateMetaBase):
    """State of the atmosphere used for atmospheric correction.

    Attributes:
    -----------
    source: str
        Source for the atmospheric data. Typically `CAMS` or `CAMS+acolite`
    variables: AtmosphericStateVariables
        Variables describing the state of the atmosphere

    """

    variables: AtmosphericStateVariables


class GeometryState(StateMetaBase):
    """Geometric state (viewing, solar, geography) used for atmospheric correction.

    Attributes:
    -----------
    source: str
        Source for the geometry data. Typically `ADCS` or `ADCS+DEM+GCP`
    variables: GeometryStateVariables
        Geometric variables describing view and altitude
    """

    variables: GeometryStateVariables


class SceneState(StateMetaBase):
    """Scene state used for atmospheric correction.

    Attributes:
    -----------
    source: str
        Source for the scene state
    variables: SceneStateVariables
        Scene variables
    """

    variables: SceneStateVariables


class AtmosphericCorrectionConfiguration(BaseModelWithUnits):
    """Configuration of the atmospheric correction used

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

    method: str | None
    atmospheric_state: AtmosphericState | None
    geometry_state: GeometryState | None
    scene_state: SceneState | None
