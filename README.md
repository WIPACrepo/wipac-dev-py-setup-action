# WIPACrepo/wipac-dev-py-setup-action

A GitHub Action Package for Automating Python-Package Setup & Maintenance

This GitHub Action prepares a repository to be GitHub-released and optionally, PyPI-published by
the [Python Semantic Release GitHub Action](https://python-semantic-release.readthedocs.io/en/latest/). A user needs
only to provide a few attributes in the GitHub Action's `with` block (see [*Configuration
Modes*](#configuration-modes)).

## Overview

This GitHub Action package generates:

- `pyproject.toml` sections needed for creating a new release on GitHub (and optionally, publishing the package to
  PyPI),
- hyper-linked badges for `README.md`, and
- `py.typed` file(s) for type-hinting.

Commits are git-pushed by the "github-actions" bot (github-actions@github.com). A different actor can used by
setting `git_committer_name` and `git_committer_email`.

## Getting Started

In order to use the action, a few files need to have the following:

1. Client repo provides:
    - Python package source code
    - GitHub Action package, see [GitHub Action YAML](#github-action-yaml) and its [inputs](#inputs)
    - `setup.py` with `setuptools.setup()`,
      *this is the entire file:*
        ```
        from setuptools import setup  # type: ignore[import]

        setup()
        ```
    - a `pyproject.toml` -- sections and attributes will be auto-inserted. Any conflicting
      sections/attributes will be overwritten.
2. Run as GitHub Action
3. Source code updates are committed and pushed by the `github-actions` bot (by default)

### GitHub Action YAML

```
  py-setup:
    runs-on: ubuntu-latest
    steps:
      - name: checkout
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.PERSONAL_ACCESS_TOKEN }}
      - uses: WIPACrepo/wipac-dev-py-setup-action@v5.#
        with:
          mode: ...
          python_min: ...
          ...
```

#### Personal Access Token

Supplying a generated personal access token (`secrets.PERSONAL_ACCESS_TOKEN`) will allow the action to push commits *and
still* trigger GH workflows. The token needs "repo" permissions.

### Inputs

The following are inputted to the GitHub Action package in its `with` block:

| Input                 | Description                                                                                                                                                                                                          | Required                           | Default                                                                |
|-----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------|------------------------------------------------------------------------|
| `mode`                | The mode corresponding to what to do:<br>-`PACKAGING`: setup packaging files, metadata, etc. for the project<br>-`PACKAGING_AND_PYPI`: everything in `PACKAGING`, plus additional metadata needed to publish to PyPI | **True**                           | -                                                                      |
| `python_min`          | Minimum required Python version                                                                                                                                                                                      | **True**                           | -                                                                      |
| `keywords_comma`      | A comma-delimited string of strings, like "WIPAC, python tools, utilities"                                                                                                                                           | _required if `pypi_name` is given_ | N/A                                                                    |
| `author`              | Author of the package                                                                                                                                                                                                | _required if `pypi_name` is given_ | N/A                                                                    |
| `author_email`        | Email of the package's author                                                                                                                                                                                        | _required if `pypi_name` is given_ | N/A                                                                    |
| `pypi_name`           | Name of the PyPI package (relevant if `mode=PACKAGING_AND_PYPI`)                                                                                                                                                     | False                              | N/A -- not providing this will bypass generating PyPI-related metadata |
| `python_max`          | Maximum supported Python version                                                                                                                                                                                     | False                              | the most recent Python release                                         |
| `package_dirs`        | Space-separated list of directories to package                                                                                                                                                                       | False                              | All packages in the repository's root directory                        |
| `exclude_dirs`        | Space-separated list of directories to exclude from release, relative to the repository's root directory                                                                                                             | False                              | `test tests doc docs resource resources example examples`              |
| `git_committer_name`  | Name used for `git config user.name`                                                                                                                                                                                 | False                              | `github-actions`                                                       |
| `git_committer_email` | Email used for `git config user.email`                                                                                                                                                                               | False                              | `github-actions@github.com`                                            |

## Configuration Modes

### `mode=PACKAGING`: Outputs for Non-PyPI Enabled Packages

The following is autogenerated for the absolute minimal input (see [inputs](#inputs)):

- `pyproject.toml` with all the original, non-conflicting sections *plus*:
  ```
    [build-system]
    requires = ["setuptools>=78.1", "setuptools-scm"]
    build-backend = "setuptools.build_meta"
    
    [project]
    dynamic = ["version"]
    name = "wipac-dev-tools"
    requires-python = ">=3.8, <3.13"
    
    [tool.setuptools.packages.find]
    namespaces = false
    exclude = ["test", "tests", "doc", "docs", "resource", "resources", "example", "examples"]
  
    [tool.setuptools_scm]
    ```
- `README.md` prepended with hyperlink-embedded badges (*note the lack of PyPI badges*):
    + [![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/WIPACrepo/wipac-dev-tools?include_prereleases)](https://github.com/WIPACrepo/wipac-dev-tools/) [![GitHub issues](https://img.shields.io/github/issues/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) [![GitHub pull requests](https://img.shields.io/github/issues-pr/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen)

### `mode=PACKAGING_AND_PYPI`: Outputs for PyPI-Enabled Packages

When the relevant inputs are given (see [inputs](#inputs)), the following is autogenerated:

- `pyproject.toml` with all the original, non-conflicting sections *plus*:
    ```
    [build-system]
    requires = ["setuptools>=78.1", "setuptools-scm"]
    build-backend = "setuptools.build_meta"
    
    [project]
    dynamic = ["version"]
    name = "wipac-dev-tools"
    description = "Common, basic, and reusable development tools"
    readme = "README.md"
    keywords = ["WIPAC", "python tools", "utilities"]
    classifiers = ["Programming Language :: Python :: 3.8", "Programming Language :: Python :: 3.9", "Programming Language :: Python :: 3.10", "Programming Language :: Python :: 3.11", "Programming Language :: Python :: 3.12"]
    requires-python = ">=3.8, <3.13"
    license-files = ["LICENSE"]
    license = "MIT"
    
    [[project.authors]]
    name = "WIPAC Developers"
    email = "developers@icecube.wisc.edu"
    
    [project.urls]
    Homepage = "https://pypi.org/project/wipac-dev-tools/"
    Tracker = "https://github.com/WIPACrepo/wipac-dev-tools/issues"
    Source = "https://github.com/WIPACrepo/wipac-dev-tools"
    
    [tool.setuptools.packages.find]
    namespaces = false
    exclude = ["test", "tests", "doc", "docs", "resource", "resources", "example", "examples"]
  
    [tool.setuptools_scm]
    ```
- `README.md` prepended with hyperlink-embedded badges:
    + [![PyPI](https://img.shields.io/pypi/v/wipac-dev-tools)](https://pypi.org/project/wipac-dev-tools/) [![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/WIPACrepo/wipac-dev-tools?include_prereleases)](https://github.com/WIPACrepo/wipac-dev-tools/) [![Versions](https://img.shields.io/pypi/pyversions/wipac-dev-tools.svg)](https://pypi.org/project/wipac-dev-tools) [![PyPI - License](https://img.shields.io/pypi/l/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/blob/main/LICENSE) [![GitHub issues](https://img.shields.io/github/issues/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) [![GitHub pull requests](https://img.shields.io/github/issues-pr/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen)

## Example GitHub Action Workflow

The [WIPACrepo/wipac-dev-actions-testbed](https://github.com/WIPACrepo/wipac-dev-actions-testbed/blob/main/.github/workflows/cicd.yml)
repository ([PyPI package](https://pypi.org/project/wipac-dev-actions-testbed/)) uses the following GitHub Action
packages:

1. [`WIPACrepo/wipac-dev-py-versions-action` _(source)_](https://github.com/WIPACrepo/wipac-dev-py-versions-action)
    - This will output all the client Python package's supported Python 3 releases.
    - Use this to parallelize tests with each Python 3 release.
1. [`WIPACrepo/wipac-dev-py-setup-action` _(source)_](https://github.com/WIPACrepo/wipac-dev-py-setup-action)
    - you are here :)
1. [`WIPACrepo/wipac-dev-py-dependencies-action`  _(
   source)_](https://github.com/WIPACrepo/wipac-dev-py-dependencies-action)
    - This bumps the client package dependencies' versions in `dependencies.log` (and similar files)
1. [`WIPACrepo/wipac-dev-next-version-action`](https://github.com/WIPACrepo/wipac-dev-next-version-action)
    - This determines the next semantic version for the repo
1. [`WIPACrepo/wipac-dev-py-build-action`](https://github.com/WIPACrepo/wipac-dev-py-build-action)
    - This builds the Python package using an injected semantic version (see above)
2. `softprops/action-gh-release` and `pypa/gh-action-pypi-publish`
    - These publish release builds to GitHub and PyPI, respectively
