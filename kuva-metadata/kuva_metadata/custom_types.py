"""Custom classes to store in Pydantic models"""

import numpy as np
from pydantic import BaseModel, ConfigDict
from rasterio.crs import CRS
from shapely import Point, Polygon, get_coordinates


class CRSGeometry(BaseModel):
    """
    Store a `shapely.geometry` together with the relevant CRS.

    Attributes
    ----------
    geom: Polygon
        Shapely polygon with the geometry
    crs_epsg: rasterio.crs.CRS
        CRS over which the polygon is represented.
    """

    geom: Polygon | Point
    crs_epsg: CRS
    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    @property
    def numpy(self) -> np.ndarray:
        """Turn the geometry into a numpy array of polygon coordinates.

        Notes
        -----
        This loses the CRS information so make sure to keep track of it elsewhere
        """
        return get_coordinates(self.geom, include_z=True).squeeze()
