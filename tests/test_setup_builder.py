"""Test setup_builder.py"""

# pylint:disable=redefined-outer-name

import os
import pathlib
import sys
import uuid
from typing import Any

import pytest

sys.path.append(".")
import setup_builder  # noqa: E402 # isort:skip # pylint:disable=import-error,wrong-import-position


GITHUB_FULL_REPO = "foobarbaz-org/foobarbaz-repo"


@pytest.fixture
def directory() -> str:
    """Get path to setup.cfg in a random testing directory."""
    _dir = f"test-dir-{uuid.uuid1()}"

    os.mkdir(_dir)
    with open(f"{_dir}/README.md", "w") as f:
        f.write("# This is a test package, it's not real\n")

    os.mkdir(f"{_dir}/mock_package")
    with open(f"{_dir}/mock_package/__init__.py", "w") as f:
        f.write("__version__ = '1.2.3'\n")

    os.mkdir(f"{_dir}/.circleci")
    pathlib.Path(f"{_dir}/.circleci/config.yml").touch()

    return _dir


def test_00(directory: str, requests_mock: Any) -> None:
    """Test using a minimum [wipac:cicd_setup_builder]."""
    setup_cfg_path = f"{directory}/setup.cfg"

    setup_cfg_in = """[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6

[options]
install_requires =
    pyjwt
    requests
    requests-futures
    tornado
    wipac-dev-tools

[options.extras_require]
telemetry =
    wipac-telemetry

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    setup_cfg_out = """[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6

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

[semantic_release]  # generated by wipac:cicd_setup_builder
version_variable = mock_package/__init__.py:__version__
upload_to_pypi = True
patch_without_tag = True
commit_parser = semantic_release.history.tag_parser
minor_tag = [minor]
fix_tag = [fix]
branch = main

[options]  # generated by wipac:cicd_setup_builder: python_requires, packages
install_requires =
    pyjwt
    requests
    requests-futures
    tornado
    wipac-dev-tools
python_requires = >=3.6, <3.11
packages = find:

[options.package_data]  # generated by wipac:cicd_setup_builder: '*'
* = py.typed

[options.extras_require]
telemetry =
    wipac-telemetry

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    setup_builder.main(setup_cfg_path, GITHUB_FULL_REPO)

    with open(setup_cfg_path) as f:
        expected = setup_cfg_out.replace("    ", "\t").split("\n")
        for actual_line in f.readlines():
            print(actual_line, end="")
        for i, actual_line in enumerate(f.readlines()):
            assert actual_line == expected[i] + "\n"
keywords_spaced = python REST tools utilities OpenTelemetry tracing telemetry

[options]
install_requires =
    pyjwt
    requests
    requests-futures
    tornado
    wipac-dev-tools

[options.extras_require]
telemetry =
    wipac-telemetry

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    setup_cfg_out = """[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6
keywords_spaced = python REST tools utilities OpenTelemetry tracing telemetry

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
    python
    REST
    tools
    utilities
    OpenTelemetry
    tracing
    telemetry
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

[semantic_release]  # generated by wipac:cicd_setup_builder
version_variable = mock_package/__init__.py:__version__
upload_to_pypi = True
patch_without_tag = True
commit_parser = semantic_release.history.tag_parser
minor_tag = [minor]
fix_tag = [fix]
branch = main

[options]  # generated by wipac:cicd_setup_builder: python_requires, packages
install_requires =
    pyjwt
    requests
    requests-futures
    tornado
    wipac-dev-tools
python_requires = >=3.6, <3.11
packages = find:

[options.package_data]  # generated by wipac:cicd_setup_builder: '*'
* = py.typed

[options.extras_require]
telemetry =
    wipac-telemetry

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    setup_builder.main(setup_cfg_path, GITHUB_FULL_REPO)

    with open(setup_cfg_path) as f:
        expected = setup_cfg_out.replace("    ", "\t").split("\n")
        for actual_line in f.readlines():
            print(actual_line, end="")
        for i, actual_line in enumerate(f.readlines()):
            assert actual_line == expected[i] + "\n"
