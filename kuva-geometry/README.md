# Kuva Geometry

The `kuva-geometry` project contains various class definitions and utility functions related 
to imaging and Earth geometry. These help in processing Kuva Space products and to provide 
additional commonly used tools.

Currently, the main use is for calculating the satellite camera rays on the Earth to get 
footprints of the imaged area.

# Table of Contents

- [Installation](#installation)
- [Tests](#tests)
- [Contributing](#contributing)
- [Configuration](#configuration)
- [Contact information](#contact-information)
- [License](#license)

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

To be added

# Contact information

For questions or support, please open an issue. If you have been given a support contact, 
feel free to send them an email explaining your issue.

# License

To be added

# Status of unit tests

[![Unit tests for kuva-geometry](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-geometry.yml/badge.svg)](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-geometry.yml)