# Contributing to Kuva Data Processing

Thank you for considering to contribute to Kuva Data Processing!

Note that contributions 
fall into the [MIT license](LICENSE.md) with the rest of the codebase.

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md) when discussing in issues and pull requests of the project.

## First things first: adding an issue

Whether you encounter a bug, something is unclear, or you believe a new functionality 
would greatly improve the lives of users of this project, please always drop an issue 
first. Issues are gone through periodically to be discussed and to be fixed in order of 
urgency.

### Issue contents

Please include the following information in your issues

- Type of issue:
    - "Bug" for any errors in the execution of code
    - "Docs" for any lack of clarity in code or README documentation
    - "Feature" for a suggestion of a feature that does not exist
- If your issue is a bug, add also the following information:
    - Full error message
    - Python version
    - Package version of `kuva-data-processing` subproject
    - Package version of any related libraries if the error stems from these libraries
    - Any extra information that might help pinpoint or solve the error

## Encountering a bug

If you encounter a bug, please leave an issue. If you already have a clear solution in mind, 
you can pair it up with a pull request (from a `bugfix` branch to `develop`) and link it 
to the issue. If it requires any larger changes in functionality, it is better to first 
discuss within the issue on possible solutions.

## Adding new functionalities

We recommend leaving an issue and letting Kuva Space developers come back to you before 
committing into large changes. This is to make sure that the functionality will be added 
to the project. This will be discussed and approved internally.

To increase likelihood of the acceptance, we recommend leaving also a rough plan on how 
to implement this new feature.

## Code quality guidelines

Our code quality follows closely the Python's PEP8 standard. The `pyproject.toml` files 
enforce the most important ones through the Ruff tool. These can be integrated into some 
IDEs to automatically format or leave notes on code when not complying.

## Coding workflow and branches

The Kuva Data Processing branches have the following naming and hierarchy order.

```
main < develop < bugfix/my-bugfix
               < feature/my-feature
```

When developing in the project, the default is creating a new branch from develop and 
doing your fix there.

In critical issues, some hotfixes may be pushed to `main` and `develop` separately. Still, 
the initial PR should be done on the `develop` branch and it will be cherry-picked to `main` 
if necessary.

# Installation from source

## Installing a virtual environment

To make installation smooth and sure to work, we recommend installing a virtual 
environment with a specific Python version, along with the Poetry program for handling Python package installing.

One example of a virtual environment manager is pyenv, which can be installed with

```bash
# Update local packages
sudo apt update -y
# Install Pyenv
curl https://pyenv.run | bash

# Then configure your bash script to recognize pyenv
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
source ~/.bashrc
```

We recommend using Python version 3.10.12 for `kuva-datareader`

```bash
# Install the Python version
pyenv install 3.10.12
# Create a virtual environment with the given Python version
pyenv virtualenv 3.10.12 kuva-env
# Activate the virtual environment
pyenv activate kuva-env
```

Python dependencies are managed by Poetry, install it to your virtual environment with

```bash
pip install poetry
```


## Installing the projects

As explained above, the installation is best done within a virtual environment using 
Poetry with the following commands (tested on **Python 3.10.14**). For example, to install 
the `kuva-reader` library, which also does have the `kuva-metadata` and `kuva-geometry` 
libraries as dependency, use the following commands:


```bash
cd kuva-reader
poetry install
```

# Tests

Unit tests are done with Pytest for each subproject separately. Most of them can be run 
as is, but `kuva-reader` has tests with real Hyperfield-1 data, and fetching the data 
requires [Git LFS](https://git-lfs.com/).

To fetch the test data yourself, you need to install Git LFS and pull the data:

```sh
# Only once per system
sudo apt-get install git-lfs
git lfs install
```

Then, you can simply download the test data with:

```sh
# Download all data
git lfs pull
```

Now, to run all of the tests succesfully, run pytest through poetry:

```sh
poetry run pytest
```

## Status of unit tests

[![Unit tests for kuva-geometry](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-geometry.yml/badge.svg?branch=main)](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-geometry.yml?branch=main)
[![Unit tests for kuva-metadata](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-metadata.yml/badge.svg?branch=main)](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-metadata.yml?branch=main)
[![Unit tests for kuva-reader](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-reader.yml/badge.svg?branch=main)](https://github.com/KuvaSpace/kuva-data-processing/actions/workflows/test-kuva-reader.yml?branch=main)


# Code documentation

To generate, serve and/or develop the code documentation you will need to activate a
virtual environment with `mkdocs` and in its associated plugins installed. You
can accomplish this by running the following on a fresh environment:

```bash
pip install mkdocs\
            mkdocs-material\
            "mkdocstrings[python]"\
            black
```

To serve the documentation locally, run the command

```bash
mkdocs serve
```

Now, connect to the given address (by default: [http://127.0.0.1:8000](http://127.0.0.1:8000)), 
and you can navigate through all the classes and functionalities available in the subprojects 
in the repository.

## *For Kuva developers: publishing the newest version in PyPi*

To publish to PyPi, follow the steps:

1. Configure PyPi credentials for Poetry if not already done
2. Verify that you are in the correct branch (*develop* or *main*)
3. `cd` into the sub-package to update
4. Review/verify code integrity and run tests
5. Update package version in the `pyproject.toml` file
6. `poetry build`
7. One last check of the generated files and current directory
8. `poetry publish`
