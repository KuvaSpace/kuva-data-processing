"""Utilities to process images related to product processing."""

import rasterio as rio
from shapely.geometry import box, Polygon
from rasterio.warp import transform_bounds


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
        # Transform the bounds to the new CRS using rasterio's built-in function
        bounds = transform_bounds(image.crs, crs, *image.bounds)
        footprint = box(*bounds)
    else:
        footprint = box(*image.bounds)
    return footprint
