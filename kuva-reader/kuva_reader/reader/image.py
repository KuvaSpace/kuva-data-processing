"""Utilities to process images related to product processing."""
import rasterio as rio
from pyproj import Transformer
from shapely import Polygon
from shapely.geometry import box


def image_footprint(image: rio.DatasetReader, crs: str = "") -> Polygon:
    """Return a product footprint as a shapely polygon

    Parameters
    ----------
    image
        The product image
    crs, optional
        CRS to convert to, by default "", keeping the image's CRS

    Returns
    -------
        A shapely polygon footprint
    """
    if crs:
        transformer = Transformer.from_crs(image.crs, crs, always_xy=True)
        bounds = image.bounds
        minx, miny = transformer.transform(bounds[0], bounds[1])
        maxx, maxy = transformer.transform(bounds[2], bounds[3])
        footprint = box(minx, miny, maxx, maxy)
    else:
        footprint = box(*image.bounds)
    return footprint
