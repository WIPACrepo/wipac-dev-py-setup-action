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
    - a `pyproject.toml` file with a `[project].version` attribute (defining `__version__` strings in
      package `__init__.py`
      file(s) is allowed). Other sections and attributes will be auto-inserted. Any conflicting
      sections/attributes will be overwritten.
2. Run as GitHub Action
3. Source code updates are committed and pushed by the `github-actions` bot (by default)

### GitHub Action YAML

```
  py-setup:
    runs-on: ubuntu-latest
    steps:
      - name: checkout
        uses: actions/checkout@v3
        with:
          token: ${{ secrets.PERSONAL_ACCESS_TOKEN }}
      - uses: WIPACrepo/wipac-dev-py-setup-action@v4.#
        with:
          python_min: ...
          ...
```

#### Personal Access Token

Supplying a generated personal access token (`secrets.PERSONAL_ACCESS_TOKEN`) will allow the action to push commits *and
still* trigger GH workflows. The token needs "repo" permissions.

### Inputs

The following are inputted to the GitHub Action package in its `with` block:

| Input                 | Description                                                                                              | Required                           | Default                                                                    |
|-----------------------|----------------------------------------------------------------------------------------------------------|------------------------------------|----------------------------------------------------------------------------|
| `python_min`          | Minimum required Python version                                                                          | **True**                           | -                                                                          |
| `keywords`            | A JSON-formatted array of strings                                                                        | _required if `pypi_name` is given_ | N/A                                                                        |
| `author`              | Author of the package                                                                                    | _required if `pypi_name` is given_ | N/A                                                                        |
| `author_email`        | Email of the package's author                                                                            | _required if `pypi_name` is given_ | N/A                                                                        |
| `pypi_name`           | Name of the PyPI package                                                                                 | False                              | N/A -- not providing this will bypass PyPI-related metadata and publishing |
| `python_max`          | Maximum supported Python version                                                                         | False                              | the most recent Python release                                             |
| `package_dirs`        | Space-separated list of directories to package                                                           | False                              | All packages in the repository's root directory                            |
| `exclude_dirs`        | Space-separated list of directories to exclude from release, relative to the repository's root directory | False                              | `test tests doc docs resource resources example examples`                  |
| `patch_without_tag`   | Whether to make a patch release even if the commit message does not explicitly warrant one               | False                              | `True`                                                                     |
| `git_committer_name`  | Name used for `git config user.name`                                                                     | False                              | `github-actions`                                                           |
| `git_committer_email` | Email used for `git config user.email`                                                                   | False                              | `github-actions@github.com`                                                |

## Configuration Modes

There are several [input attributes](#inputs). However, these broadly can be grouped into two subsets, or two "modes":
[PyPI enabled](#outputs-for-pypi-enabled-packages)
and [non-PyPI enabled](#outputs-for-non-pypi-enabled-packages).

### Outputs for PyPI-Enabled Packages

When the `pypi_name` input is `True` and other relevant inputs are given (see [inputs](#inputs)), the following is
autogenerated:

- `pyproject.toml` with all the original, non-conflicting sections *plus*:
    ```
    [build-system]
    requires = ["setuptools>=61.0"]
    build-backend = "setuptools.build_meta"
    
    [project]
    version = "1.2.3"
    name = "wipac-dev-tools"
    description = "Common, basic, and reusable development tools"
    readme = "README.md"
    keywords = ["WIPAC", "python", "tools", "utilities"]
    classifiers = ["Development Status :: 5 - Production/Stable", "Programming Language :: Python :: 3.8", "Programming Language :: Python :: 3.9", "Programming Language :: Python :: 3.10", "Programming Language :: Python :: 3.11", "Programming Language :: Python :: 3.12"]
    requires-python = ">=3.8, <3.13"
    
    [[project.authors]]
    name = "WIPAC Developers"
    email = "developers@icecube.wisc.edu"
    
    [project.license]
    file = "LICENSE"
    
    [project.urls]
    Homepage = "https://pypi.org/project/wipac-dev-tools/"
    Tracker = "https://github.com/WIPACrepo/wipac-dev-tools/issues"
    Source = "https://github.com/WIPACrepo/wipac-dev-tools"
    
    [tool.semantic_release]
    version_toml = ["pyproject.toml:project.version"]
    version_variables = ["wipac_dev_tools/__init__.py:__version__"] 
    commit_parser = "emoji"
    
    [tool.semantic_release.commit_parser_options]
    major_tags = ["[major]"]
    minor_tags = ["[minor]", "[feature]"]
    patch_tags = ["[patch]", "[fix]", " ", "!", "#", "$", "%", "&", "'", "(", ")", "*", "+", "-", ".", "/", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?", "@", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "[", "]", "^", "_", "`", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "{", "|", "}", "~"]
    
    [tool.setuptools.package-data]
    "*" = ["py.typed"]
    
    [tool.setuptools.packages.find]
    namespaces = false
    exclude = ["test", "tests", "doc", "docs", "resource", "resources", "example", "examples"]
    ```
- `README.md` prepended with hyperlink-embedded badges:
    + [![CircleCI](https://img.shields.io/circleci/build/github/WIPACrepo/wipac-dev-tools)](https://app.circleci.com/pipelines/github/WIPACrepo/wipac-dev-tools?branch=main&filter=all) [![PyPI](https://img.shields.io/pypi/v/wipac-dev-tools)](https://pypi.org/project/wipac-dev-tools/) [![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/WIPACrepo/wipac-dev-tools?include_prereleases)](https://github.com/WIPACrepo/wipac-dev-tools/) [![Versions](https://img.shields.io/pypi/pyversions/wipac-dev-tools.svg)](https://pypi.org/project/wipac-dev-tools) [![PyPI - License](https://img.shields.io/pypi/l/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/blob/main/LICENSE) [![GitHub issues](https://img.shields.io/github/issues/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) [![GitHub pull requests](https://img.shields.io/github/issues-pr/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen)
    + Note: The CircleCI badge is only auto-generated if the client repo uses CircleCI.

#### Note on PyPI's Python Classifier "Development Status"

This is determined by auto-detecting the package's current version. If (1) the git commit message is intending to
trigger
Semantic Release's version bumping action, (2) the `patch_without_tag` is not `False`, and (3) the new version will
qualify for
a new "Development Status", then that Status is used ahead of time.

### Outputs for Non-PyPI Enabled Packages

The following is autogenerated for the absolute minimal input (see [inputs](#inputs)):

- `pyproject.toml` with all the original, non-conflicting sections *plus*:
  ```
    [build-system]
    requires = ["setuptools>=61.0"]
    build-backend = "setuptools.build_meta"
    
    [project]
    version = "1.2.3"
    name = "wipac-dev-tools"
    requires-python = ">=3.8, <3.13"
    
    [tool.semantic_release]
    version_toml = ["pyproject.toml:project.version"]
    version_variables = ["wipac_dev_tools/__init__.py:__version__"]
    commit_parser = "emoji"
    
    [tool.semantic_release.commit_parser_options]
    major_tags = ["[major]"]
    minor_tags = ["[minor]", "[feature]"]
    patch_tags = ["[patch]", "[fix]", " ", "!", "#", "$", "%", "&", "'", "(", ")", "*", "+", "-", ".", "/", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?", "@", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "[", "]", "^", "_", "`", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "{", "|", "}", "~"]
    
    [tool.setuptools.package-data]
    "*" = ["py.typed"]
    
    [tool.setuptools.packages.find]
    namespaces = false
    exclude = ["test", "tests", "doc", "docs", "resource", "resources", "example", "examples"]
    ```
- `README.md` prepended with hyperlink-embedded badges (*note the lack of PyPI badges*):
    + [![CircleCI](https://img.shields.io/circleci/build/github/WIPACrepo/wipac-dev-tools)](https://app.circleci.com/pipelines/github/WIPACrepo/wipac-dev-tools?branch=main&filter=all) [![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/WIPACrepo/wipac-dev-tools?include_prereleases)](https://github.com/WIPACrepo/wipac-dev-tools/) [![GitHub issues](https://img.shields.io/github/issues/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) [![GitHub pull requests](https://img.shields.io/github/issues-pr/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen)
    + Note: The CircleCI badge is only auto-generated if the client repo uses CircleCI.

## Example GitHub Action Workflow

The [wipac-dev-tools](https://github.com/WIPACrepo/wipac-dev-tools/blob/main/.github/workflows/wipac-cicd.yml)
repository ([PyPI package](https://pypi.org/project/wipac-dev-tools/)) uses the following GitHub Action
packages:

1. [`WIPACrepo/wipac-dev-py-versions-action` _(source)_](https://github.com/WIPACrepo/wipac-dev-py-versions-action)
    - This will output all the client Python package's supported Python 3 releases.
    - Use this to parallelize tests with each Python 3 release.
1. [`WIPACrepo/wipac-dev-py-setup-action` _(source)_](https://github.com/WIPACrepo/wipac-dev-py-setup-action)
    - you are here :)
1. [`WIPACrepo/wipac-dev-py-dependencies-action`  _(
   source)_](https://github.com/WIPACrepo/wipac-dev-py-dependencies-action)
    - This bumps the client package dependencies' versions in `dependencies.log` (and similar files)
1. [`python-semantic-release/python-semantic-release` _(
   source)_](https://python-semantic-release.readthedocs.io/en/latest/)
    - This will make a new GitHub Release and a PyPI Release (if not disabled with `patch_without_tag = False`).
