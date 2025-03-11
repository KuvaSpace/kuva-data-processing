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

Please include the following things in your issues

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
