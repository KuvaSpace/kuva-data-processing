<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/1d8b44f1-1999-4cfb-8744-32871056c253">
    <img alt="kuva-space-logo" src="https://github.com/user-attachments/assets/d8f47cc8-1491-4d0c-a8cf-318ea7e0afdc" width="50%">
  </picture>
</div>

# Reader for Kuva Space images

The reader project allows the reading of Kuva Space products from any part of its processing chain.

The Kuva Space images are in GeoTIFF format. The products consist of an image or multiple 
images along with its metadata to give all the necessary information to use the products. 
The metadata lives either in a Kuva Space database, or alternatively in a sidecar JSON file. 

This library allows the reading of the image GeoTIFFs into `rasterio.DatasetReader` objects that 
allow convenient raster manipulations, along with their `kuva-metadata` metadata objects.

# Installation

```bash
pip install kuva-reader
``` 

### Requirements

`Python 3.10` to `3.13`, preferably within a virtual environment

# Code

## Minimal example

This is a minimal example that allows you to read and print the image shape of a L2 product.

The result product is in this case an L2A product (as seen from the folder name).
The loaded product is stored in a `rasterio.DatasetReader` object, which contains extensive GIS functionalities [(examples for usage)](https://rasterio.readthedocs.io/en/stable/api/rasterio.io.html#rasterio.io.DatasetReader).

```python
from kuva_reader import read_product

product = read_product("my_data_folder/hyperfield1a_L2A_20250105T092548")
print(product)  # Will show some main information such as image shape and CRS
```

This assumes a mostly untouched folder after distributing. Otherwise, you may need to
read the product manually based on the product processing level:

```python
from kuva_reader import Level2AProduct

l2a_product = Level2AProduct("your/l2a/folder")
```

The actual raster image is stored and can be analysed in `product.image`, while metadata
information of the product is in `product.metadata`.

## Other tips

The product object attributes and methods allow the retrieval of other interesting information as well:

```python
from kuva_reader import read_product

product = read_product("your/product/folder")
product.footprint(crs="EPSG:4326")  # Footprint with option to transform CRS
product.image.shape  # The image attribute contains all the image data
product.wavelengths  # Wavelengths corresponding to image bands
product.crs  # CRS
```

## Processing levels

Currently the reader supports the following processing levels for Kuva products:

- **L0**: Radiometrically corrected frames as TOA radiance
- **L1AB**: Band-aligned product formed from multiple L0 products
- **L1C**: Georeferences and orthorectified L1 product
- **L2A**: Atmospherically corrected product as BOA reflectance

## Special tags

All images generated by Kuva Space should have the following special tags added to the
geotiff metadata.
- `_KUVA_PRODUCT_LEVEL`: A string, e.g, `"0"` describing the level of the product.
- `_KUVA_PRODUCT_ID`: The id on the database for the product associated with the geotiff.

This makes it very easy to pinpoint what product we are dealing with and works around
the issue that our images are not a monolithic entity but rather just folders that can
be messed with.

# Contributing

Please follow the guidelines in [CONTRIBUTING.md](https://github.com/KuvaSpace/kuva-data-processing/blob/main/CONTRIBUTING.md).

Also, please follow our [Code of Conduct](https://github.com/KuvaSpace/kuva-data-processing/blob/main/CODE_OF_CONDUCT.md)
while discussing in the issues and pull requests.

# Contact information

For questions or support, please open an issue. If you have been given a support contact, 
feel free to send them an email explaining your issue.

# License

The `kuva-reader` project software is under the [MIT license](https://github.com/KuvaSpace/kuva-data-processing/blob/main/LICENSE.md).

# Status of unit tests

[![Unit tests for kuva-reader](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-reader.yml/badge.svg)](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-reader.yml)
