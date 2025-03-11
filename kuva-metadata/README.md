# Kuva Metadata

Images taken from a satellite are complicated beasts with lot of metadata associated
to them. This repository contains the metadata definitions for the Hyperfield products. 
This metadata along with the acquired GeoTIFF images form the Kuva Space products in its 
various processing levels.

With the metadata and images, we may process products to the 
next processing levels, or do more precise processing than just with a GeoTIFF. 


# Table of Contents

- [Processing Levels](#processing-levels)
- [Architecture](#architecture)
- [Installation](#installation)
- [Tests](#tests)
- [Contributing](#contributing)
- [Configuration](#configuration)
- [Contact information](#contact-information)
- [License](#license)


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

# Installation

### Requirements

- Python 3.10, preferably within a virtual environment

### Installation from source

Installation from source is simply done with poetry. Be sure to activate your Python 
virtual environment and run the following command in this project's root:

```sh
# If poetry is not installed in your virtual environment:
pip install poetry
```

```sh
# Install the package locally
poetry install
```

Pypi installation coming soon.

# Tests

Units tests aimed for the package developers are available with Pytest. Running pytest 
requires the dev dependencies of the project. They can be installed with

```sh
# Test dependency installation
poetry install --with dev
```

Then, tests can be run simply with pytest in the project's root folder

```sh
# Running tests
poetry run pytest
```

# Contributing

Please follow the guidelines in [CONTRIBUTING.md](../CONTRIBUTING.md).

Also, please follow our [Code of Conduct](../CODE_OF_CONDUCT.md) while discussing in the 
issues and pull requests.

# Contact information

For questions or support, please open an issue. If you have been given a support contact, 
feel free to send them an email explaining your issue.

# License

The `kuva-metadata` project software is under the [MIT license](../LICENSE.md).

# Status of unit tests

[![Unit tests for kuva-metadata](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-metadata.yml/badge.svg)](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-metadata.yml)