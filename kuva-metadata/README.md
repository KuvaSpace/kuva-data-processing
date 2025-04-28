<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/1d8b44f1-1999-4cfb-8744-32871056c253">
    <img alt="kuva-space-logo" src="https://github.com/user-attachments/assets/d8f47cc8-1491-4d0c-a8cf-318ea7e0afdc" width="50%">
  </picture>
</div>

# Kuva Metadata

Images taken from a satellite are complicated beasts with lot of metadata associated
to them. This repository contains the metadata definitions for the Hyperfield products. 
This metadata along with the acquired GeoTIFF images form the Kuva Space products in its 
various processing levels.

With the metadata and images, we may process products to the 
next processing levels, or do more precise processing than just with a GeoTIFF. 

# Installation

```bash
pip install kuva-metadata
``` 

This package is also included when installing the `kuva-reader`.

### Requirements

`Python 3.10` to `3.13`, preferably within a virtual environment

# Processing levels

Currently there are metadata definitions for the following processing levels of Kuva products:

- **L0**: Radiometrically corrected frames as TOA radiance
- **L1AB**: Band-aligned product formed from multiple L0 products
- **L1C**: Georeferences and orthorectified L1 product
- **L2A**: Atmospherically corrected product as BOA reflectance

# Architecture

All the metadata are defined as Pydantic models, this has several advantages:

- A very rich set of validations that are applied before data object construction
- The ability to easily (de)serialize (from)to JSON

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

[![Unit tests for kuva-metadata](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-metadata.yml/badge.svg)](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-metadata.yml)