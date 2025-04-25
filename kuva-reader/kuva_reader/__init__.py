"""
Kuva Reader provides functionality for opening and accessing Kuva Space Earth
Observation (EO) products.  The module handles the reading and parsing of image
data, as well as extracting and structuring the associated metadata to
facilitate further analysis or visualization.

Key Features

- Open EO Products: Load satellite images and corresponding metadata from
  various dataformats.
- Access Metadata: Retrieve information such as acquisition time, satellite
  name, sensor type, geospatial coordinates, and any custom metadata embedded
  within the product.
- Image Handling: Manage the loading  of image data for efficient use in
  analytical processes.

Dependencies
- kuva-metadata: A specialized library that handles the extraction and
  parsing of metadata associated with Kuva Space products.
- xarray: Used for loading image data as arrays with extra functionality,
  including labeled coordinates and metadata, which is useful for analysis and
  visualization.
"""

__version__ = "0.1.0"

from .reader.image import (
    image_to_dtype_range,
    image_to_original_range,
    image_to_uint16_range,
)
from .reader.level0 import Level0Product
from .reader.level1 import Level1ABProduct, Level1CProduct
from .reader.level2 import Level2AProduct
from .reader.read import read_product

__all__ = [
    "Level0Product",
    "Level1ABProduct",
    "Level1CProduct",
    "Level2AProduct",
    "image_to_dtype_range",
    "image_to_original_range",
    "image_to_uint16_range",
    "read_product",
]
