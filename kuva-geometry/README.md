<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../docs/images/logo_kuva_space_white.png">
    <img alt="kuva-space-logo" src="../docs/images/logo_kuva_space_black.png" width="50%">
  </picture>
</div>

# Kuva Geometry

The `kuva-geometry` project contains various class definitions and utility functions related 
to imaging and Earth geometry. These help in processing Kuva Space products and to provide 
additional commonly used tools.

Currently, the main use is for calculating the satellite camera rays on the Earth to get 
footprints of the imaged area.

# Table of Contents

- [Installation](#installation)
- [Contributing](#contributing)
- [Configuration](#configuration)
- [Contact information](#contact-information)
- [License](#license)

# Installation

```bash
pip install kuva-geometry
``` 

This package is also included when installing the `kuva-reader`.

### Requirements

`Python 3.10` to `3.13`, preferably within a virtual environment

# Contributing

Please follow the guidelines in [CONTRIBUTING.md](../CONTRIBUTING.md).

Also, please follow our [Code of Conduct](../CODE_OF_CONDUCT.md) while discussing in the 
issues and pull requests.

# Contact information

For questions or support, please open an issue. If you have been given a support contact, 
feel free to send them an email explaining your issue.

# License

The `kuva-geometry` project software is under the [MIT license](../LICENSE.md).

# Status of unit tests

[![Unit tests for kuva-geometry](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-geometry.yml/badge.svg)](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-geometry.yml)