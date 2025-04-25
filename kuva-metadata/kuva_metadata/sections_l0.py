"""Metadata specification for L0 products"""

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, cast

import networkx as nx
import numpy as np
from networkx.readwrite import json_graph
from pint import Quantity
from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
    SerializationInfo,
    ValidationInfo,
    field_serializer,
    field_validator,
)
from quaternion import quaternion
from shapely import Point, Polygon

# Unused imports so that common objects are available with one import
from kuva_metadata.sections_common import (  # noqa # pylint: disable=unused-import
    BaseModelWithUnits,
    Header,
    MetadataBase,
    Satellite,
)

from .custom_types import CRSGeometry
from .geometry_utils import frame_footprint, frame_ray_Earth_intersections
from .serializers import (
    serialize_CRSGeometry,
    serialize_graph,
    serialize_quantity,
    serialize_quaternion,
)
from .validators import (
    check_is_utc_datetime,
    must_be_angle,
    must_be_distance,
    must_be_positive_distance,
    must_be_positive_time,
    must_be_pressure,
    must_be_speed,
    must_be_temperature,
    parse_crs_geometry,
    parse_date,
    parse_quaternion,
)


class Weather(BaseModelWithUnits):
    """Weather information at the center point of the acquisition.

    Note
    ----
    When using this information keep in mind that you are assigning a single weather
    data point acquired from some more or less reliable weather station to an image that
    may span 50 km across. The variables below may change A LOT over such distances!

    Attributes
    ----------
    timestamp
        Timestamp for the requested weather data
    temperature
        Ground temperature
    pressure
        Pressure
    humidity
        Relative humidity
    wind_speed
        Wind speed
    wind_dir
        Dominant wind direction
    """

    timestamp: datetime
    temperature: Quantity
    pressure: Quantity
    humidity: Annotated[float, Field(strict=True, ge=0, le=1)]
    wind_speed: Quantity
    wind_dir: Quantity

    _parse_timestamp = field_validator("timestamp", mode="before")(parse_date)
    _check_tz = field_validator("timestamp")(check_is_utc_datetime)
    _check_temp = field_validator("temperature", mode="before")(must_be_temperature)
    _check_press = field_validator("pressure", mode="before")(must_be_pressure)
    _check_angle = field_validator("wind_dir", mode="before")(must_be_angle)
    _check_speed = field_validator("wind_speed", mode="before")(must_be_speed)
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    @field_serializer(
        "temperature", "pressure", "wind_speed", "wind_dir", when_used="json"
    )
    def _serialize_quantity(self, q: Quantity):
        return serialize_quantity(q)


class AlignmentAlgorithm(BaseModel):
    """The name of an alignment algorithm and a dict with its parameters

    Attributes
    ----------
    name
        Alignment algorithm name
    parameters
        Parameters used by the alignment algorithm to align products.
    """

    name: str
    parameters: dict[str, Any]


class AlignmentParameters(BaseModel):
    """Parameters used in the alignment routines to generate homography matrices to
    align and stitch frames/bands/cubes/products.

    Attributes
    ----------
    frame_alignment_mode
        Algorithm mode used. If the first algorithm from the list fails
        the second is applied as fallback method. If the second fails...
    band_alignment_mode
        Algorithm mode used. If the first algorithm from the list fails
        the second is applied as fallback method. If the second fails...
    cube_alignment_mode
        Algorithm mode used. If the first algorithm from the list fails
        the second is applied as fallback method. If the second fails...
    product_stitching_mode
        Algorithm mode used. If the first algorithm from the list fails
        the second is applied as fallback method. If the second fails...
    cube_alignment_reference_cube
        The key to the datacube on the `Image` that is the reference for the cube
        alignment.
    product_stitching_reference_cube
        The key to the datacube on the `Image` that is the reference for the product
        stitching.
    frame_alignment_reference_position_percent
        The relative position (in %) of the reference frame, within the band.
    band_alignment_reference_frames
        The reference frame that is used to align the bands.
    cube_alignment_reference_frames
        The reference frames that are used to align each cube to the reference cube. If
        a frame index for the reference cube is passed it will be ignored.
    product_stitching_reference_frame
        The frame inside the product stitching reference cube that is used to stitch
        l0_products into a sequence.
    product_stitching_cube_order
        A list of camera names with the order of the camera names specifying the order
        in which the cubes of the sequence will be stored in the L1 product.
    band_alignment_use_snr_enhanced_frames_by_stacking
        Whether to first enhance the SNR of the alignment frames by stacking them.
    cube_alignment_use_snr_enhanced_frames_by_stacking
        Whether to first enhance the SNR of the alignment frames by stacking them.
    product_stitching_use_snr_enhanced_frames_by_stacking
        Whether to first enhance the SNR of the alignment frames by stacking them.
    """

    # The alignment algorithms
    frame_alignment_mode: Annotated[list[AlignmentAlgorithm], Field(min_length=1)]
    band_alignment_mode: Annotated[list[AlignmentAlgorithm], Field(min_length=1)]
    cube_alignment_mode: Annotated[list[AlignmentAlgorithm], Field(min_length=1)]
    product_stitching_mode: Annotated[list[AlignmentAlgorithm], Field(min_length=1)]

    # The reference frames
    frame_alignment_reference_position_percent: Annotated[
        int, Field(ge=0, le=100, strict=True)
    ]
    band_alignment_reference_position_percent: Annotated[
        int, Field(ge=0, le=100, strict=True)
    ]
    cube_alignment_reference_position_percent: Annotated[
        int, Field(ge=0, le=100, strict=True)
    ]
    product_stitching_reference_position_percent: Annotated[
        int, Field(ge=0, le=100, strict=True)
    ]

    # The reference bands
    band_alignment_reference_bands: dict[str, Annotated[int, Field(ge=0, strict=True)]]
    cube_alignment_reference_bands: dict[str, Annotated[int, Field(ge=0, strict=True)]]
    product_stitching_reference_band: Annotated[int, Field(ge=0, strict=True)]

    # The reference cubes
    cube_alignment_reference_cube: str
    product_stitching_reference_cube: str

    # The cube/camera order in which the cubes in the L1 product will be stored
    product_stitching_cube_order: Annotated[list[str], Field(min_length=1)]

    # Config to decide whether frames should be stacked
    band_alignment_use_snr_enhanced_frames_by_stacking: bool
    cube_alignment_use_snr_enhanced_frames_by_stacking: bool
    product_stitching_use_snr_enhanced_frames_by_stacking: bool

    model_config = ConfigDict(validate_assignment=True)


class RadiometricCalibration(BaseModel):
    """Metadata for radiometric calibration that can be associated with an L0 product

    Attributes
    ----------
    id
        Calibration ID that identifies the calibration on the DB
    start_date
        Starting date from when the calibration is considered active
    is_validated
        Validation status on whether calibration is in use
    camera_name
        Name of the camera the calibration was done on
    lab_radcal_results
        Results from laboratory measurements, for now as a dict
    on_orbit_radcal_results
        Results from on-orbit radiometric measurements, for now as a dict, or empty for
        recently launched satellites.
    """

    id: UUID4
    start_date: datetime
    is_validated: bool
    camera_name: str
    lab_radcal_results: dict
    on_orbit_radcal_results: dict | None

    _parse_timestamp = field_validator("start_date", mode="before")(parse_date)
    _check_tz = field_validator("start_date")(check_is_utc_datetime)
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)


class Camera(BaseModelWithUnits):
    """Camera information

    Attributes
    ----------
    id
        Camera ID that identifies the camera on the DB.
    name
        Short name for the camera
    passband_range
        Wavelength range supported by the camera.
    pixel_width
        Distance between center of two sensor columns in meters.
    pixel_height
        Distance between center of two sensor rows in meters.
    focal_distance
        In meters
    n_rows
        Number of rows on sensor
    n_cols
        Number of columns on sensor
    sensor_wrt_sat_axis_quaternion
        Quaternion describing the orientation of the sensor relative to the body frame
        axis of the satellite. The coordinate system of the sensor is defined as
        follows: z-axis points outside of the light receiving face of the sensor,
        y-axis is parallel to sensor columns and increases from top to bottom (note:
        opposite to how 2D arrays are usually indexed), x-axis is parallel to sensor
        rows and grows from left to right (note: some way cols are indexed on an array)
    radiometric_calibration
        Latest radiometric calibration associated with the current camera. None is
        allowed for camera usage without need for calibrations.
    """

    id: UUID4
    name: str
    passband_range: tuple[Quantity, Quantity]
    pixel_width: Quantity
    pixel_height: Quantity
    focal_distance: Quantity
    n_rows: Annotated[int, Field(gt=0, strict=True)]
    n_cols: Annotated[int, Field(gt=0, strict=True)]
    sensor_wrt_sat_axis_quaternion: quaternion
    radiometric_calibration: RadiometricCalibration | None = None

    @field_validator("passband_range", mode="before")
    @classmethod
    def _must_be_ordered_and_to_nm(cls, v):
        v_0 = must_be_distance(v[0])
        v_1 = must_be_distance(v[1])
        if v_0 >= v_1:
            msg = "The elements of the passband range must be ordered."
            raise ValueError(msg)

        return (v_0.to("nm"), v_1.to("nm"))

    _check_f_distance = field_validator("focal_distance", mode="before")(
        must_be_positive_distance
    )
    _check_px = field_validator("pixel_width", "pixel_height", mode="before")(
        must_be_positive_distance
    )
    _check_quaternion = field_validator(
        "sensor_wrt_sat_axis_quaternion", mode="before"
    )(parse_quaternion)
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    @property
    def width(self) -> Quantity:
        """Width of a the sensor array"""
        return self.n_cols * self.pixel_width

    @property
    def height(self) -> Quantity:
        """Height of a the sensor array"""
        return self.n_rows * self.pixel_height

    @property
    def H(self) -> Quantity:
        """alias for `height`"""
        return self.height

    @property
    def W(self) -> Quantity:
        """alias for `width`"""
        return self.width

    @field_serializer("sensor_wrt_sat_axis_quaternion", when_used="json")
    def _serialize_quaternion(self, q: quaternion):
        return serialize_quaternion(q)

    @field_serializer("passband_range", when_used="json")
    def _serialize_passband_range(self, q: tuple[Quantity, Quantity]):
        return (serialize_quantity(q[0]), serialize_quantity(q[1]))

    @field_serializer("pixel_width", "pixel_height", "focal_distance", when_used="json")
    def _serialize_quantity(self, q: Quantity):
        return serialize_quantity(q)


class Frame(BaseModelWithUnits):
    """Frame metadata.

    Attributes
    ----------
    index
        Index associated with the frame (0-indexed), within a band.
    start_acquisition_date
        Timestamp of the trigger of the acquisition of the frame.
    end_acquisition_date
        Timestamp for the end of the acquisition of the frame.
    integration_time
        Integration time in seconds for the frame. Duration may be slightly different
        from `end_acquisition_time - start_acquisition_time` due to timing issues.
    sat_ecef_orientation
        Orientation quaternion of the spacecraft at the start of frame acquisition.
    position
        ECEF geodetic coordinates (estimated from telemetry) of the position of the
        spacecraft in at the start of frame acquisition (SRID=4978).
    """

    index: Annotated[int, Field(ge=0, strict=True)]
    start_acquisition_date: datetime
    end_acquisition_date: datetime
    integration_time: Quantity
    sat_ecef_orientation: quaternion
    position: CRSGeometry

    _check_int_time = field_validator("integration_time", mode="before")(
        must_be_positive_time
    )
    _parse_quaternion = field_validator("sat_ecef_orientation", mode="before")(
        parse_quaternion
    )
    _parse_timestamp = field_validator(
        "end_acquisition_date", "start_acquisition_date", mode="before"
    )(parse_date)
    _check_tz = field_validator("end_acquisition_date", "start_acquisition_date")(
        check_is_utc_datetime
    )
    _parse_geom = field_validator("position", mode="before")(parse_crs_geometry)
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    def footprint(self, camera: Camera) -> Polygon:
        """Get the ground footprint of a frame if it were taken by camera"""
        camera_footprint = frame_footprint(self, camera, use_negative_sensor_plane=True)

        return camera_footprint

    def target(self, camera: Camera) -> Point:
        """Get the ground coordinates of the central pixel of the frame"""
        target = frame_ray_Earth_intersections(np.array([[0, 0]]), self, camera)[0]
        return target

    @field_serializer("sat_ecef_orientation", when_used="json")
    def _serialize_quaternion(self, q: quaternion):
        return serialize_quaternion(q)

    @field_serializer("integration_time", when_used="json")
    def _serialize_quantity(self, q: Quantity):
        return serialize_quantity(q)

    @field_serializer("position")
    def _serialize_CRSGeometry(self, p: CRSGeometry):
        return serialize_CRSGeometry(p)


class Band(BaseModelWithUnits):
    """Band metadata.

    Attributes
    ----------
    index
        Index associated with the band (0-indexed), within a datacube.
    wavelength
        Nominal wavelength associated with the Fabry-Perot Interferometer position.
    setpoints
        Setpoint used by acquisition in the satellite. This may differ from requested
        setpoints due to e.g. internal temperature.
    start_acquisition_date
        Timestamp of the trigger of the first frame in the band.
    end_acquisition_date
        Timestamp for the end of the acquisition of the last frame in the band.
    frames
        A list with the frames.
    reference_frame_index
        Index of the frame within the band (0-indexed) that was used in the computation
         of homographies.
    """

    index: Annotated[int, Field(ge=0, strict=True)]
    wavelength: Quantity
    setpoints: tuple[int, int, int]
    start_acquisition_date: datetime
    end_acquisition_date: datetime
    frames: list[Frame]
    reference_frame_index: Annotated[int, Field(ge=0, strict=True)] | None = None

    _check_wavelength = field_validator("wavelength", mode="before")(
        must_be_positive_distance
    )
    _parse_timestamp = field_validator(
        "end_acquisition_date", "start_acquisition_date", mode="before"
    )(parse_date)
    _check_tz = field_validator("end_acquisition_date", "start_acquisition_date")(
        check_is_utc_datetime
    )
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    @field_serializer("wavelength", when_used="json")
    def _serialize_quantity(self, q: Quantity):
        return serialize_quantity(q)

    @property
    def n_frames(self) -> int:
        """Number of frames in the band"""
        return len(self.frames)

    def __len__(self) -> int:
        """Return the number of frames"""
        return self.n_frames

    def __getitem__(self, frame_idx) -> Frame:
        """Return a frame at index `frame_idx`."""
        return self.frames[frame_idx]


class DataCube(BaseModelWithUnits):
    """Metadata for a single datacube and its camera.

    Attributes
    ----------
    camera
        Camera information
    start_acquisition_date
        Timestamp of the camera trigger
    end_acquisition_date
        Timestamp of the last frame trigger
    bands
        A dict with the bands. Not necessarily ordered with respect to the band index
    reference_band_index
        Index of the band within the image file (0-indexed) that was used in the
        computation of homographies.
    """

    camera: Camera
    start_acquisition_date: datetime
    end_acquisition_date: datetime
    bands: list[Band]
    reference_band_index: Annotated[int, Field(ge=0, strict=True)] | None = None

    _parse_timestamp = field_validator(
        "end_acquisition_date", "start_acquisition_date", mode="before"
    )(parse_date)
    _check_tz = field_validator("end_acquisition_date", "start_acquisition_date")(
        check_is_utc_datetime
    )
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    @property
    def n_bands(self) -> int:
        """Number of bands in the cube"""
        return len(self.bands)

    def frame_footprint(self, band_index, frame_index) -> Polygon:
        """Get the footprint associated with one of the frames"""
        footprint = frame_footprint(self[band_index][frame_index], self.camera)

        return footprint

    def __getitem__(self, band_idx) -> Band:
        """Return a band at index `band_idx`."""
        return self.bands[band_idx]


class Image(BaseModelWithUnits):
    """Metadata associated with all the images produced on each acquisition of the
    camera array.
    All cameras are triggered simultaneously but some may finish acquisitin sooner
    since the number of frames, integration times are variable.

    Attributes
    ----------
    start_acquisition_date
        Timestamp of the camera triggers
    end_acquisition_date
        Timestamp of the last frame of the last camera trigger
    s3_path
        Path on the storage to the folder/zip containing the data
    intra_sequence_id
        A counter indicating what position within the run of images the metadata file
        is associated with.
    local_solar_zenith_angle
        The angle between the local (to the observation point) zenith and the sun.
    local_solar_azimuth_angle
        The azimuth angle between the local observation point and the sun.
    local_viewing_angle
        The angle between the satellite's pointing direction and nadir.
    acquisition_mode
        Acquisition mode of the satellite.
    footprint
        Shapely polygon describing an estimated footprint of the satellite
    data_cubes
        The data cubes that were taken during image acquisition.
    alignment_graph
        Graph where each node corresponds to a Frame and each edge to a homography
        that aligns two frames. The graph must be directed to account for the inverse
        transform.
    measured_quantity_name
        The name of the measured quantity. E.g. `TOA RADIANCE`.
    measured_quantity_unit
        The unit of the measured quantity. E.g. `W/m²/st/nm`.
    """

    start_acquisition_date: datetime
    end_acquisition_date: datetime
    s3_path: Path
    intra_sequence_id: Annotated[int, Field(ge=0, strict=True)]
    local_solar_zenith_angle: Quantity
    local_solar_azimuth_angle: Quantity
    local_viewing_angle: Quantity
    acquisition_mode: str
    footprint: CRSGeometry
    data_cubes: dict[str, DataCube]
    alignment_graph: nx.DiGraph | None
    measured_quantity_name: str
    measured_quantity_unit: str

    _check_angle = field_validator(
        "local_solar_zenith_angle",
        "local_solar_azimuth_angle",
        "local_viewing_angle",
        mode="before",
    )(must_be_angle)
    _parse_timestamp = field_validator(
        "end_acquisition_date", "start_acquisition_date", mode="before"
    )(parse_date)
    _check_tz = field_validator("end_acquisition_date", "start_acquisition_date")(
        check_is_utc_datetime
    )
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    _parse_geom = field_validator("footprint", mode="before")(parse_crs_geometry)

    @field_validator("alignment_graph", mode="before")
    @classmethod
    def _check_graph(
        cls, g: dict[Any, Any] | None, info: ValidationInfo
    ) -> nx.DiGraph | None:
        if g is None:
            return None
        # On assignment / writing
        if isinstance(g, nx.DiGraph):
            return g
        # On reading in (from sidecar (-> str) or database (-> dict))
        elif isinstance(g, (str, dict)):
            if isinstance(g, dict):
                data = g
            else:
                if info.context is None:
                    e_ = "Graph wasn't available in context"
                    raise ValueError(e_)

                image_path = cast(Path, info.context["image_path"])
                with (image_path / g).open("r") as fh:
                    data = json.loads(fh.read())

            # JSON only knows about strings but they are not hashable and therefore not
            # valid as networkX node indices. We must recover the tuples!
            data["nodes"] = [node | {"id": tuple(node["id"])} for node in data["nodes"]]
            data["adjacency"] = [
                [edge | {"id": tuple(edge["id"])} for edge in node]
                for node in data["adjacency"]
            ]
            out = cast(nx.DiGraph, json_graph.adjacency_graph(data=data, directed=True))

            # Deserialize the matrices into numpy arrays again
            numpy_edges = {
                edge_idx: {"H": np.array(edge["H"]), "status": edge["status"]}
                for edge_idx, edge in out.edges.items()
            }

            # Check that all the matrices are 3x3 as a safety net
            for edge_dict in numpy_edges.values():
                H = edge_dict["H"]

                if not H.shape == (3, 3):
                    msg = f"Only 3x3 matrices should be accepted, got {H.shape}"
                    raise ValueError(msg)

            nx.set_edge_attributes(out, numpy_edges)

            return out
        else:
            msg = "Can't parse non-string into DiGraph"
            raise ValueError(msg)

    @field_serializer(
        "local_solar_zenith_angle",
        "local_solar_azimuth_angle",
        "local_viewing_angle",
        when_used="json",
    )
    def _serialize_quantity(self, q: Quantity):
        return serialize_quantity(q)

    @field_serializer("footprint")
    def _serialize_CRSGeometry(self, p: CRSGeometry):
        return serialize_CRSGeometry(p)

    @field_serializer("alignment_graph")
    def _serialize_graph(
        self, g: nx.DiGraph | None, info: SerializationInfo
    ) -> str | None:
        if info.context is None:
            e_ = "Graph context wasn't available during graph serialization"
            raise ValueError(e_)
        return serialize_graph(g, info.context)


class MetadataLevel0(MetadataBase):
    """Metadata for Level 0 products

    Attributes
    ----------
    MetadataBase attributes
        All attributes included in parent MetadataBase
    alignment_parameters
        Parameters of the product alignment algorithm
    """

    image: Image
    alignment_parameters: AlignmentParameters

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
