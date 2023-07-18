# WIPACrepo/wipac-dev-py-setup-action
GitHub Action Package for Automating Python-Package Setup & Maintenance



## Overview
This GitHub Action prepares a repository to be GitHub-released and PyPI-published by the [Python Semantic Release GitHub Action](https://python-semantic-release.readthedocs.io/en/latest/). All that a user needs to do is define a few attributes in `setup.cfg` (see [*Main Configuration Modes*](#main-configuration-modes)).

### Details
- `setup.cfg` sections needed for publishing a package to PyPI are auto-generated,
- hyper-linked badges are added to the `README.md`,
- the root directory's `dependencies.log` is overwritten/updated (by way of [pip-compile](https://github.com/jazzband/pip-tools)) along with dedicated `dependencies-EXTRA.txt` files for each package "extra", and
- `py.typed` files are created as needed.
Commits are git-pushed by the "github-actions" bot (github-actions@github.com) by default, or your chosen actor configured by inputs (`git_committer_name` & `git_committer_email`).

#### GitHub Action Syntax
```
  py-setup:
    runs-on: ubuntu-latest
    steps:
      - name: checkout
        uses: actions/checkout@v3
        with:
          token: ${{ secrets.PERSONAL_ACCESS_TOKEN }}
      - uses: WIPACrepo/wipac-dev-py-setup-action@v#.#
```

#### Personal Access Token
Supplying a generated personal access token (`secrets.PERSONAL_ACCESS_TOKEN`) will allow the action to push commits *and still* trigger GH workflows. The token needs "repo" permissions.

#### Defining Python Package Dependencies
These go in the `setup.cfg` file's `[options]` section:
```
 [options]
 install_requires =
    package-a
    package-b
```

#### Defining Package Metadata
These are inputted as attributes in the `setup.cfg` file's `[wipac:cicd_setup_builder]` section (see [*Main Configuration Modes*](#main-configuration-modes)) and as GitHub Action inputs (see [*Input Arguments in GitHub Action*](#input-arguments-in-github-action)). All other metadata is pulled in programmatically by parsing the repo's directory tree.



## Main Configuration Modes

### Full-Metadata Mode: Generate PyPI Metadata
This will generate `setup.cfg` sections needed for making a GitHub release for your Python package and publishing it to PyPI.

1. You define:
    - `setup.cfg` with the `[wipac:cicd_setup_builder]` section and `[options].install_requires` list, like:
        ```
        [wipac:cicd_setup_builder]
        pypi_name = wipac-mock-package
        python_min = 3.6
        author = WIPAC Developers
        author_email = developers@icecube.wisc.edu
        keywords_spaced = foo bar baz

        [options]
        install_requires =
            requests
            typing_extensions

        <your other sections for non-wipac-dev-py-setup-action reasons>
        ```
    - `setup.py` with `setuptools.setup()`:
        *This is the entire `setup.py` file:*
        ```
        from setuptools import setup  # type: ignore[import]

        setup()
        ```
2. Run as GitHub Action
3. You get:
    - `setup.cfg` with all the original sections *plus*:
        ```
        [metadata]  # generated by wipac:cicd_setup_builder: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
        name = wipac-mock-package
        version = attr: mock_package.__version__
        url = https://github.com/foobarbaz-org/foobarbaz-repo
        author = WIPAC Developers
        author_email = developers@icecube.wisc.edu
        description = Ceci n’est pas une pipe
        long_description = file: README.md
        long_description_content_type = text/markdown
        keywords =
            foo
            bar
            baz
            WIPAC
            IceCube
        license = MIT
        classifiers =
            Development Status :: 5 - Production/Stable
            License :: OSI Approved :: MIT License
            Programming Language :: Python :: 3.6
            Programming Language :: Python :: 3.7
            Programming Language :: Python :: 3.8
            Programming Language :: Python :: 3.9
            Programming Language :: Python :: 3.10
        download_url = https://pypi.org/project/wipac-mock-package/
        project_urls =
            Tracker = https://github.com/foobarbaz-org/foobarbaz-repo/issues
            Source = https://github.com/foobarbaz-org/foobarbaz-repo

        [semantic_release]  # fully-generated by wipac:cicd_setup_builder
        version_variable = mock_package/__init__.py:__version__
        upload_to_pypi = True
        patch_without_tag = True
        commit_parser = semantic_release.history.tag_parser
        minor_tag = [minor]
        fix_tag = [fix]
        branch = main

        [options]  # generated by wipac:cicd_setup_builder: python_requires, packages
        install_requires =
            requests
            typing_extensions
        python_requires = >=3.6, <3.11
        packages = find:

        [options.package_data]  # generated by wipac:cicd_setup_builder: '*'
        * = py.typed

        [options.packages.find]  # generated by wipac:cicd_setup_builder: include/exclude
        exclude =
            test
            tests
            doc
            docs
            resource
            resources

        <your other sections for non-wipac-dev-py-setup-action reasons>
        ```
    - `README.md` prepended with hyperlink-embedded badges:
        + [![CircleCI](https://img.shields.io/circleci/build/github/WIPACrepo/wipac-dev-tools)](https://app.circleci.com/pipelines/github/WIPACrepo/wipac-dev-tools?branch=main&filter=all) [![PyPI](https://img.shields.io/pypi/v/wipac-dev-tools)](https://pypi.org/project/wipac-dev-tools/) [![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/WIPACrepo/wipac-dev-tools?include_prereleases)](https://github.com/WIPACrepo/wipac-dev-tools/) [![PyPI - License](https://img.shields.io/pypi/l/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/blob/main/LICENSE) [![Lines of code](https://img.shields.io/tokei/lines/github/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/) [![GitHub issues](https://img.shields.io/github/issues/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) [![GitHub pull requests](https://img.shields.io/github/issues-pr/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen)
        + Note: The CircleCI badge is only auto-generated if your repo uses CircleCI.
    - `dependencies.log` generated (overwritten) by [pip-compile](https://github.com/jazzband/pip-tools) using `[options].install_requires` in `setup.cfg`:
        ```
        #
        # This file is autogenerated by pip-compile with python 3.8
        # To update, run:
        #
        #    pip-compile
        #
        certifi==2021.10.8
            # via requests
        charset-normalizer==2.0.12
            # via requests
        idna==3.3
            # via requests
        requests==2.27.1
            # via wipac-dev-tools (setup.py)
        typing-extensions==4.2.0
            # via wipac-dev-tools (setup.py)
        urllib3==1.26.9
            # via requests
        ```

#### Note: Python's Classifier "Development Status"
This is determined by auto-detecting the package's current version. If the git commit message is intending to trigger Semantic Release's version bumping action and the new version will qualify for a new "Development Status", then that Status is used ahead of time.


### Minimal Mode: No PyPI Metadata
This will generate the absolute minimal sections needed for making a release for your Python package.

1. You define:
    - `setup.cfg` with the `[wipac:cicd_setup_builder]` section and `[options].install_requires` list, like:
        ```
        [wipac:cicd_setup_builder]
        python_min = 3.6

        [options]
        install_requires =
            requests
            typing_extensions

        <your other sections for non-wipac-dev-py-setup-action reasons>
        ```
    - `setup.py` with `setuptools.setup()`:
        *This is the entire `setup.py` file:*
        ```
        from setuptools import setup  # type: ignore[import]

        setup()
        ```
2. Run as GitHub Action
3. You get:
    - `setup.cfg` with all the original sections *plus* (*note `upload_to_pypi = False` and the truncated `[metadata]` section*):
        ```
        [metadata]  # generated by wipac:cicd_setup_builder: version
        version = attr: mock_package.__version__

        [semantic_release]  # fully-generated by wipac:cicd_setup_builder
        version_variable = mock_package/__init__.py:__version__
        upload_to_pypi = False
        patch_without_tag = True
        commit_parser = semantic_release.history.tag_parser
        minor_tag = [minor]
        fix_tag = [fix]
        branch = main

        [options]  # generated by wipac:cicd_setup_builder: python_requires, packages
        install_requires =
            requests
            typing_extensions
        python_requires = >=3.6, <3.11
        packages = find:

        [options.package_data]  # generated by wipac:cicd_setup_builder: '*'
        * = py.typed

        [options.packages.find]  # generated by wipac:cicd_setup_builder: include/exclude
        exclude =
            test
            tests
            doc
            docs
            resource
            resources

        <your other sections for non-wipac-dev-py-setup-action reasons>
        ```
    - `README.md` prepended with hyperlink-embedded badges (*note the lack of PyPI badges*):
        + [![CircleCI](https://img.shields.io/circleci/build/github/WIPACrepo/wipac-dev-tools)](https://app.circleci.com/pipelines/github/WIPACrepo/wipac-dev-tools?branch=main&filter=all) [![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/WIPACrepo/wipac-dev-tools?include_prereleases)](https://github.com/WIPACrepo/wipac-dev-tools/) [![Lines of code](https://img.shields.io/tokei/lines/github/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/) [![GitHub issues](https://img.shields.io/github/issues/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) [![GitHub pull requests](https://img.shields.io/github/issues-pr/WIPACrepo/wipac-dev-tools)](https://github.com/WIPACrepo/wipac-dev-tools/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen)
        + Note: The CircleCI badge is only auto-generated if your repo uses CircleCI.
    - `dependencies.log` generated (overwritten) by [pip-compile](https://github.com/jazzband/pip-tools) using `[options].install_requires` in `setup.cfg`:
        ```
        #
        # This file is autogenerated by pip-compile with python 3.8
        # To update, run:
        #
        #    pip-compile
        #
        certifi==2021.10.8
            # via requests
        charset-normalizer==2.0.12
            # via requests
        idna==3.3
            # via requests
        requests==2.27.1
            # via wipac-dev-tools (setup.py)
        typing-extensions==4.2.0
            # via wipac-dev-tools (setup.py)
        urllib3==1.26.9
            # via requests
        ```


## Advanced Usage Options

### Additional Attributes in `setup.cfg`/`[wipac:cicd_setup_builder]`

#### `python_max`
Use this to pin the maximum compatible Python 3 release version. This will change `[options].python_requires` and `[metadata].classifiers` (if PyPI-metadata mode is enabled). Defining a max version is generally discouraged since new Python 3 versions are usually backward-compatible. Use this if there's a troublesome package requirement.
- Default: None

#### `package_dirs`
Use this to explicitly define directories for packaging. This is a space-separated list of directories to package. This generates a `[options.packages.find].include` list for the given packages and sub-packages. Without this, a list is generated for `[options.packages.find].exclude`, which will exclude commonly non-released directories (see [*directory-exclude*](#directory-exclude)).
- **NOTE:** *Multi-package/multi-directory packaging is not currently supported (https://github.com/wipacrepo/wipac-dev-py-setup-action/issues/15)*
- Default: N/A

#### `keywords_spaced`
Using this list is generally encouraged for PyPI-published packages as it helps with SEO. However, technically, `[wipac:cicd_setup_builder].keywords_spaced` is optional. Any "base keywords" are automatically added regardless, see [*Input Arguments in GitHub Action*](#input-arguments-in-github-action).
- Default: None


### Input Arguments in GitHub Action
#### `base-keywords`
A list of keywords to add to `[metadata]`, space-delimited. These are aggregated with those given in `[wipac:cicd_setup_builder].keywords_spaced`. This is a good place to add organization-standard keywords (as opposed to repo-specific keywords).
- Default: None

#### `directory-exclude`
A list of directories to exclude from release, space-delimited.
- Default: 'test tests doc docs resource resources'

#### `license`
The repo's license type.
- Default: 'MIT'


## Full CI-Workflow: Using Alongside Other GitHub Actions
The `wipac-dev-py-setup-action` GitHub Action pairs well with other GitHub Actions, including [WIPACrepo/wipac-dev-py-versions-action](https://github.com/WIPACrepo/wipac-dev-py-versions-action) and [relekang/python-semantic-release](https://python-semantic-release.readthedocs.io/en/latest/). These can be linked to create a robust CI/CD workflow for packaging, testing, and publishing.

### Example: Linking Actions as Jobs with Dependencies
#### Overview
*See [Example YAML](#example-yaml) for implementation details*
1. Run linters (ex: flake8, mypy)
    - To speed things up, don't include job-dependencies for linters.
2. Use `WIPACrepo/wipac-dev-py-setup-action`
    - This...
        + sets up your Python package metadata in `setup.cfg`,
        + bumps package dependencies' versions in `dependencies.log`, and/or
        + updates `README.md`.
    - *The bot's git-push will cancel pending steps/jobs and trigger another workflow.*
3. Use `WIPACrepo/wipac-dev-py-versions-action`
    - This will `pip install` your Python package with each supported Python 3 version.
    - This will catch install errors before any tests run.
4. Run unit and integration tests
    - To limit startup costs, include a job-dependency for the previous jobs. This will guarantee tests are running with the most recently bumped package dependencies.
5. Use `relekang/python-semantic-release`
    - This will make a new GitHub Release and a PyPI Release (if not disabled).
    - This should use an `"if"`-constraint for the default branch (main or master).

#### Example YAML
```
name: example ci/cd

on: [push]

jobs:

  <your linters>

  py-setup:
    runs-on: ubuntu-latest
    steps:
      # Checks-out your repository under $GITHUB_WORKSPACE, so your job can access it
      - name: checkout
        uses: actions/checkout@v3
        with:
          token: ${{ secrets.PERSONAL_ACCESS_TOKEN }}
      - uses: WIPACrepo/wipac-dev-py-setup-action@v#.#

  py-versions:
    needs: [py-setup]
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.versions.outputs.matrix }}
    steps:
      - uses: actions/checkout@v3
      - id: versions
        uses: WIPACrepo/wipac-dev-py-versions-action@v#.#

  <your unit tests>

  <your integration tests>

  release:
    if: ${{ github.ref == 'refs/heads/master' || github.ref == 'refs/heads/main' }}
    needs: [py-setup, pip-install, tests]
    runs-on: ubuntu-latest
    concurrency: release
    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0
    - name: Python Semantic Release
      uses: relekang/python-semantic-release@master
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        repository_username: __token__
        repository_password: ${{ secrets.PYPI_TOKEN }}
```
