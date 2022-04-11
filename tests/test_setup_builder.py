"""Test setup_builder.py"""

# pylint:disable=redefined-outer-name

import os
import sys
import uuid

import pytest

sys.path.append(".")
import setup_builder  # noqa: E402 # isort:skip # pylint:disable=import-error,wrong-import-position


@pytest.fixture
def setup_cfg_path() -> str:
    """Get path to setup.cfg in a random testing directory."""
    _dir = f"test-dir-{uuid.uuid1()}"

    os.mkdir(_dir)
    with open(f"{_dir}/README.md", "w") as f:
        f.write("# This is a test package, it's not real\n")

    os.mkdir(f"{_dir}/my_package")
    with open(f"{_dir}/my_package/__init__.py", "w") as f:
        f.write("__version__ = 'X.Y.Z'\n")

    return f"{_dir}/setup.cfg"


def test_00(setup_cfg_path: str) -> None:
    """Test using a standard setup.cfg."""

    setup_cfg_in = """[wipac:cicd_setup_builder]
pypi_name = wipac-rest-tools
python_min = 3.6
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
pypi_name = wipac-rest-tools
python_min = 3.6
keywords_spaced = python REST tools utilities OpenTelemetry tracing telemetry

[metadata]  # generated by wipac:cicd_setup_builder
name = wipac-rest-tools
version = attr: rest_tools.__version__
url = https://github.com/WIPACrepo/rest-tools
author = WIPAC Developers
author_email = developers@icecube.wisc.edu
description = REST tools in python - common code for client and server
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
download_url = https://pypi.org/project/wipac-rest-tools/
project_urls =
    Tracker = https://github.com/WIPACrepo/rest-tools/issues
    Source = https://github.com/WIPACrepo/rest-tools

[semantic_release]  # generated by wipac:cicd_setup_builder
version_variable = rest_tools/__init__.py:__version__
upload_to_pypi = True
patch_without_tag = True
commit_parser = semantic_release.history.tag_parser
minor_tag = [minor]
fix_tag = [fix]
branch = master

[options]  # generated by wipac:cicd_setup_builder: 'python_requires', 'packages'
python_requires = >=3.6, <3.11
packages = find:
install_requires =
    pyjwt
    requests
    requests-futures
    tornado
    wipac-dev-tools

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

    setup_builder.main(setup_cfg_path, "")

    with open(setup_cfg_path) as f:
        out = setup_cfg_out.split("\n")
        for i, line in enumerate(f.readlines()):
            assert line == out[i] + "\n"
