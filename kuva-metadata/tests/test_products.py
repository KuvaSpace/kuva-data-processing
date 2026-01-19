import datetime
from pathlib import Path
from typing import cast

import pytest
import quaternion
from pint import UnitRegistry
from rasterio.crs import CRS
from shapely import Point, from_wkt

from kuva_metadata.custom_types import CRSGeometry
from kuva_metadata.sections_common import swap_ureg_in_instance
from kuva_metadata.sections_l0 import Band, Frame


@pytest.fixture(scope="module")
def ureg() -> UnitRegistry:
    """Unit Registry to be used in tests"""
    return UnitRegistry()


@pytest.fixture
def test_data_path() -> Path:
    return Path(__file__).parent / "test_data"


@pytest.fixture
def band_metadata(ureg) -> Band:
    """A synthetic band metadata object"""
    utc = datetime.timezone.utc
    frames = [
        Frame(
            index=0,
            start_acquisition_date=datetime.datetime(2025, 1, 1, 12, 0, 0, tzinfo=utc),
            end_acquisition_date=datetime.datetime(
                2025, 1, 1, 12, 0, 0, 50, tzinfo=utc
            ),
            integration_time=1 * ureg.us,
            sat_ecef_orientation=quaternion.quaternion(0, 0, 0, 0),
            position=CRSGeometry(
                geom=cast(
                    Point,
                    from_wkt(
                        "POINT Z (1282374.8999436763 -5181851.839868248 4328138.614476594)"
                    ),
                ),
                crs_epsg=CRS.from_epsg(4978),
            ),
        )
    ]
    band = Band(
        index=0,
        wavelength=500 * ureg.nm,
        setpoints=(12345, 23456, 34567),
        start_acquisition_date=datetime.datetime(2025, 1, 1, 12, 0, 0, tzinfo=utc),
        end_acquisition_date=datetime.datetime(2025, 1, 1, 12, 0, 1, tzinfo=utc),
        frames=frames,
    )
    return band


def test_metadata_python_load(band_metadata):
    """Check that a metadata object is correctly initialized from Python"""
    assert band_metadata.frames[0].index == 0


def test_metadata_json_load(test_data_path):
    """Check that a metadata object is correctly validated from JSON"""
    with (test_data_path / "band_metadata.json").open() as fh:
        band_json_data = fh.read()
    band = Band.model_validate_json(band_json_data)
    band_with_ureg = Band.model_validate_json_with_ureg(band_json_data, UnitRegistry())

    assert band.frames[0].integration_time.to("s").magnitude == 1.2
    assert band_with_ureg.frames[0].integration_time.to("s").magnitude == 1.2


def test_ureg_swap(ureg, band_metadata):
    """Swapping of Unit Registries works with nested metadata objects"""
    # Arithmetic operations should be compatible if uregs are the same
    frame_int = band_metadata.frames[0].integration_time
    same_band = cast(Band, swap_ureg_in_instance(band_metadata, ureg))
    assert frame_int + same_band.frames[0].integration_time > 0

    # Arithmetic operations should fail if uregs are different
    other_ureg = UnitRegistry()
    new_band = cast(Band, swap_ureg_in_instance(band_metadata, other_ureg))
    with pytest.raises(ValueError):
        _ = frame_int + new_band.frames[0].integration_time
