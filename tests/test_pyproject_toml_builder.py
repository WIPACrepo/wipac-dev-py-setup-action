"""Test pyproject_toml_builder.py"""

import copy
import logging
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest
import tomlkit
from tomlkit import TOMLDocument

LOGGER = logging.getLogger(__name__)


sys.path.append(".")
import pyproject_toml_builder  # noqa: E402 # isort:skip # pylint:disable=import-error,wrong-import-position


#
# CONSTANTS
#


GITHUB_FULL_REPO = "foobarbaz-org/foobarbaz-repo"
AUTHOR = "WIPAC Developers"
AUTHOR_EMAIL = "developers@icecube.wisc.edu"
BASE_KEYWORDS = ["WIPAC", "IceCube"]
EXCLUDE_DIRS = [
    "test",
    "tests",
    "doc",
    "docs",
    "resource",
    "resources",
    "example",
    "examples",
]
TOKEN = "token"


#
# VANILLA SECTIONS
#


VANILLA_SECTIONS_IN = {
    "project": {
        "dependencies": sorted(
            [
                "pyjwt",
                "requests",
                "requests-futures",
                "tornado",
                "wipac-dev-tools",
            ]
        ),
        "optional-dependencies": {
            "telemetry": [
                "wipac-telemetry",
            ],
            "best-tools": sorted(["pen", "paper", "hard-work"]),
        },
    },
}

BUILD_SYSTEM_SECTION = {
    "build-system": {
        "requires": ["setuptools>=78.1", "setuptools-scm"],
        "build-backend": "setuptools.build_meta",
    },
}

PYPI_URLS_KEYVALS = {
    "urls": {
        "Homepage": "https://pypi.org/project/wipac-mock-package/",
        "Tracker": "https://github.com/foobarbaz-org/foobarbaz-repo/issues",
        "Source": "https://github.com/foobarbaz-org/foobarbaz-repo",
    }
}

VANILLA_PROJECT_KEYVALS_OUT = {
    **VANILLA_SECTIONS_IN["project"],
    "authors": [{"name": AUTHOR, "email": AUTHOR_EMAIL}],
    "description": "Ceci n’est pas une pipe",
    "readme": "README.md",
    "license": {"file": "LICENSE"},
    "requires-python": ">=3.6, <3.12",
    "dynamic": ["version"],
}
NO_PYPI_VANILLA_PROJECT_KEYVALS_OUT = {  # even MORE vanilla than vanilla
    k: v
    for k, v in VANILLA_PROJECT_KEYVALS_OUT.items()
    if k in ["dependencies", "optional-dependencies", "requires-python"]
}


################################################################################
# HELPER FUNCTIONS
################################################################################


def assert_outputted_pyproject_toml(
    pyproject_toml_path: Path, expected: dict[str, Any]
) -> None:
    """Compare each's contents casted to a dict."""

    # sanity test
    doc = TOMLDocument()
    for key, value in expected.items():
        doc[key] = value

    print()
    print("EXPECTED TOML OUTPUT:")
    print(expected)

    print()
    print("ACTUAL TOML OUTPUT:")
    with open(pyproject_toml_path) as f:
        actual = tomlkit.load(f)
        print(actual)

    print()
    assert expected == actual


################################################################################
# FIXTURES
################################################################################


@pytest.fixture
def directory() -> Path:
    """Get path to pyproject.toml in a random testing directory."""
    _dir = Path(f"test-dir-{uuid.uuid1()}")

    os.mkdir(_dir)
    with open(_dir / "README.md", "w") as f:
        f.write("# This is a test package, it's not real\n")

    os.mkdir(_dir / "mock_package")
    Path(_dir / "mock_package/__init__.py").touch()

    print(_dir)
    return _dir


def mock_many_requests(requests_mock: Any) -> None:
    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get(
        "https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json",
        json=[
            {
                "version": "3.12.0-rc.3",
                "stable": False,
                "release_url": "https://github.com/actions/python-versions/releases/tag/3.12.0-rc.3-6237742040",
                "files": [
                    {
                        "filename": "python-3.12.0-rc.3-darwin-arm64.tar.gz",
                        "arch": "arm64",
                        "platform": "darwin",
                        "download_url": "https://github.com/actions/python-versions/releases/download/3.12.0-rc.3-6237742040/python-3.12.0-rc.3-darwin-arm64.tar.gz",
                    },
                    {
                        "filename": "python-3.12.0-rc.3-darwin-x64.tar.gz",
                        "arch": "x64",
                        "platform": "darwin",
                        "download_url": "https://github.com/actions/python-versions/releases/download/3.12.0-rc.3-6237742040/python-3.12.0-rc.3-darwin-x64.tar.gz",
                    },
                ],
            },
            {
                "version": "3.11.5",
                "stable": True,
                "release_url": "https://github.com/actions/python-versions/releases/tag/3.11.5-5999813088",
                "files": [
                    {
                        "filename": "python-3.11.5-darwin-arm64.tar.gz",
                        "arch": "arm64",
                        "platform": "darwin",
                        "download_url": "https://github.com/actions/python-versions/releases/download/3.11.5-5999813088/python-3.11.5-darwin-arm64.tar.gz",
                    },
                    {
                        "filename": "python-3.11.5-darwin-x64.tar.gz",
                        "arch": "x64",
                        "platform": "darwin",
                        "download_url": "https://github.com/actions/python-versions/releases/download/3.11.5-5999813088/python-3.11.5-darwin-x64.tar.gz",
                    },
                ],
            },
            {
                "version": "3.10.13",
                "stable": True,
                "release_url": "https://github.com/actions/python-versions/releases/tag/3.10.13-5997403688",
                "files": [
                    {
                        "filename": "python-3.10.13-darwin-x64.tar.gz",
                        "arch": "x64",
                        "platform": "darwin",
                        "download_url": "https://github.com/actions/python-versions/releases/download/3.10.13-5997403688/python-3.10.13-darwin-x64.tar.gz",
                    },
                    {
                        "filename": "python-3.10.13-linux-20.04-x64.tar.gz",
                        "arch": "x64",
                        "platform": "linux",
                        "platform_version": "20.04",
                        "download_url": "https://github.com/actions/python-versions/releases/download/3.10.13-5997403688/python-3.10.13-linux-20.04-x64.tar.gz",
                    },
                ],
            },
        ],
    )


################################################################################
# TESTS
################################################################################


def test_00_minimum_input(directory: Path, requests_mock: Any) -> None:
    """Test using bare minimum input."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = directory / "pyproject.toml"

    gha_input = pyproject_toml_builder.GHAInput(
        auto_mypy_option=False,
        python_min=(3, 6),
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        tomlkit.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        **BUILD_SYSTEM_SECTION,
        "project": {
            "name": "mock-package",
            **NO_PYPI_VANILLA_PROJECT_KEYVALS_OUT,  # the true minimum is more vanilla than vanilla)
        },
        "tool": {
            "setuptools_scm": {},
            "setuptools": {
                "package-data": {"*": ["py.typed"]},
                "packages": {"find": {"exclude": EXCLUDE_DIRS, "namespaces": False}},
            },
        },
    }

    # run pyproject_toml_builder
    pyproject_toml_builder.work(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_01_minimum_input_w_pypi(directory: Path, requests_mock: Any) -> None:
    """Test using the minimum input with pypi attrs."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = directory / "pyproject.toml"

    gha_input = pyproject_toml_builder.GHAInput(
        auto_mypy_option=False,
        pypi_name="wipac-mock-package",
        python_min=(3, 6),
        keywords=["WIPAC", "IceCube"],
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        tomlkit.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        **BUILD_SYSTEM_SECTION,
        "project": {
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS_OUT,
            "keywords": ["WIPAC", "IceCube"],
            "classifiers": [
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
            ],
            **PYPI_URLS_KEYVALS,
        },
        "tool": {
            "setuptools_scm": {},
            "setuptools": {
                "package-data": {"*": ["py.typed"]},
                "packages": {"find": {"exclude": EXCLUDE_DIRS, "namespaces": False}},
            },
        },
    }

    # run pyproject_toml_builder
    pyproject_toml_builder.work(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_10_keywords(directory: Path, requests_mock: Any) -> None:
    """Test using  `keywords`."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = directory / "pyproject.toml"

    gha_input = pyproject_toml_builder.GHAInput(
        auto_mypy_option=False,
        pypi_name="wipac-mock-package",
        python_min=(3, 6),
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        keywords=[
            "python",
            "REST",
            "tools",
            "REST tools",
            "utilities",
            "OpenTelemetry",
            "tracing",
            "telemetry",
            "3+ word string keywords",
        ],
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        tomlkit.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        **BUILD_SYSTEM_SECTION,
        "project": {
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS_OUT,
            "keywords": [
                "python",
                "REST",
                "tools",
                "REST tools",
                "utilities",
                "OpenTelemetry",
                "tracing",
                "telemetry",
                "3+ word string keywords",
            ],
            "classifiers": [
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
            ],
            **PYPI_URLS_KEYVALS,
        },
        "tool": {
            "setuptools_scm": {},
            "setuptools": {
                "package-data": {"*": ["py.typed"]},
                "packages": {"find": {"exclude": EXCLUDE_DIRS, "namespaces": False}},
            },
        },
    }

    # run pyproject_toml_builder
    pyproject_toml_builder.work(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_20_python_max(directory: Path, requests_mock: Any) -> None:
    """Test using  `python_max`."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = directory / "pyproject.toml"

    gha_input = pyproject_toml_builder.GHAInput(
        auto_mypy_option=False,
        pypi_name="wipac-mock-package",
        python_min=(3, 6),
        python_max=(3, 9),
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        keywords=[
            "python",
            "REST",
            "tools",
            "utilities",
            "OpenTelemetry",
            "tracing",
            "telemetry",
        ],
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        tomlkit.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        **BUILD_SYSTEM_SECTION,
        "project": {
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS_OUT,
            "requires-python": ">=3.6, <3.10",  # override VANILLA_PROJECT_KEYVALS
            "keywords": [
                "python",
                "REST",
                "tools",
                "utilities",
                "OpenTelemetry",
                "tracing",
                "telemetry",
            ],
            "classifiers": [
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
            ],
            **PYPI_URLS_KEYVALS,
        },
        "tool": {
            "setuptools_scm": {},
            "setuptools": {
                "package-data": {"*": ["py.typed"]},
                "packages": {"find": {"exclude": EXCLUDE_DIRS, "namespaces": False}},
            },
        },
    }

    # run pyproject_toml_builder
    pyproject_toml_builder.work(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_30_package_dirs__single(directory: Path, requests_mock: Any) -> None:
    """Test using `package_dirs` & a single desired package."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = directory / "pyproject.toml"

    gha_input = pyproject_toml_builder.GHAInput(
        auto_mypy_option=False,
        pypi_name="wipac-mock-package",
        python_min=(3, 6),
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        package_dirs=["mock_package"],
        keywords=[
            "python",
            "REST",
            "tools",
            "utilities",
            "OpenTelemetry",
            "tracing",
            "telemetry",
        ],
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        tomlkit.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        **BUILD_SYSTEM_SECTION,
        "project": {
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS_OUT,
            "keywords": [
                "python",
                "REST",
                "tools",
                "utilities",
                "OpenTelemetry",
                "tracing",
                "telemetry",
            ],
            "classifiers": [
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
            ],
            **PYPI_URLS_KEYVALS,
        },
        "tool": {
            "setuptools_scm": {},
            "setuptools": {
                "package-data": {"*": ["py.typed"]},
                "packages": {
                    "find": {"include": ["mock_package", "mock_package.*"]},
                },
            },
        },
    }

    # make an extra package *not* to be included
    os.mkdir(directory / "mock_package_test")
    Path(directory / "mock_package_test/__init__.py").touch()

    # run pyproject_toml_builder
    pyproject_toml_builder.work(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_34_package_dirs__multi_autoname__no_pypi(
    directory: Path, requests_mock: Any
) -> None:
    """Test using `package_dirs` & multiple desired packages."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = directory / "pyproject.toml"

    gha_input = pyproject_toml_builder.GHAInput(
        auto_mypy_option=False,
        python_min=(3, 6),
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        package_dirs=["mock_package", "another_one"],
        keywords=[
            "python",
            "REST",
            "tools",
            "utilities",
            "OpenTelemetry",
            "tracing",
            "telemetry",
        ],
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        tomlkit.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        **BUILD_SYSTEM_SECTION,
        "project": {
            "name": "mock-package-another-one",
            **NO_PYPI_VANILLA_PROJECT_KEYVALS_OUT,  # the true minimum is more vanilla than vanilla
            "authors": [{"name": AUTHOR, "email": AUTHOR_EMAIL}],
            "keywords": [
                "python",
                "REST",
                "tools",
                "utilities",
                "OpenTelemetry",
                "tracing",
                "telemetry",
            ],
        },
        "tool": {
            "setuptools_scm": {},
            "setuptools": {
                "package-data": {"*": ["py.typed"]},
                "packages": {
                    "find": {
                        "include": [
                            "mock_package",
                            "another_one",
                            "mock_package.*",
                            "another_one.*",
                        ]
                    },
                },
            },
        },
    }

    # make an extra package *not* to be included
    os.mkdir(directory / "mock_package_test")
    Path(directory / "mock_package_test/__init__.py").touch()

    # make an extra package *TO BE* included
    os.mkdir(directory / "another_one")
    Path(directory / "another_one/__init__.py").touch()

    # run pyproject_toml_builder
    pyproject_toml_builder.work(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_35_package_dirs__multi(directory: Path, requests_mock: Any) -> None:
    """Test using `package_dirs` & multiple desired packages."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = directory / "pyproject.toml"

    gha_input = pyproject_toml_builder.GHAInput(
        auto_mypy_option=False,
        pypi_name="wipac-mock-package",
        python_min=(3, 6),
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        package_dirs=["mock_package", "another_one"],
        keywords=[
            "python",
            "REST",
            "tools",
            "utilities",
            "OpenTelemetry",
            "tracing",
            "telemetry",
        ],
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        tomlkit.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        **BUILD_SYSTEM_SECTION,
        "project": {
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS_OUT,
            "keywords": [
                "python",
                "REST",
                "tools",
                "utilities",
                "OpenTelemetry",
                "tracing",
                "telemetry",
            ],
            "classifiers": [
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
            ],
            **PYPI_URLS_KEYVALS,
        },
        "tool": {
            "setuptools_scm": {},
            "setuptools": {
                "package-data": {"*": ["py.typed"]},
                "packages": {
                    "find": {
                        "include": [
                            "mock_package",
                            "another_one",
                            "mock_package.*",
                            "another_one.*",
                        ]
                    },
                },
            },
        },
    }

    # make an extra package *not* to be included
    os.mkdir(directory / "mock_package_test")
    Path(directory / "mock_package_test/__init__.py").touch()

    # make an extra package *TO BE* included
    os.mkdir(directory / "another_one")
    Path(directory / "another_one/__init__.py").touch()

    # run pyproject_toml_builder
    pyproject_toml_builder.work(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_36_package_dirs__multi_missing_init__error(
    directory: Path, requests_mock: Any
) -> None:
    """Test using `package_dirs` & multiple desired packages."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = directory / "pyproject.toml"

    gha_input = pyproject_toml_builder.GHAInput(
        auto_mypy_option=False,
        pypi_name="wipac-mock-package",
        python_min=(3, 6),
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        package_dirs=["mock_package", "another_one"],
        keywords=[
            "python",
            "REST",
            "tools",
            "utilities",
            "OpenTelemetry",
            "tracing",
            "telemetry",
        ],
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        tomlkit.dump(VANILLA_SECTIONS_IN, f)

    # make an extra package *not* to be included
    os.mkdir(directory / "mock_package_test")
    Path(directory / "mock_package_test/__init__.py").touch()

    # make an extra package *TO BE* included
    os.mkdir(directory / "another_one")

    # run pyproject_toml_builder
    with pytest.raises(
        Exception,
        match=re.escape(
            "Package directory not found: another_one (defined in pyproject.toml). "
            "Is the directory missing an __init__.py?"
        ),
    ):
        pyproject_toml_builder.work(
            pyproject_toml_path,
            GITHUB_FULL_REPO,
            TOKEN,
            gha_input,
        )


def test_40_extra_stuff(directory: Path, requests_mock: Any) -> None:
    """Test using extra stuff."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = directory / "pyproject.toml"

    gha_input = pyproject_toml_builder.GHAInput(
        auto_mypy_option=False,
        pypi_name="wipac-mock-package",
        python_min=(3, 6),
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        keywords=[
            "python",
            "REST",
            "tools",
            "utilities",
            "OpenTelemetry",
            "tracing",
            "telemetry",
        ],
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        extra_stuff: dict[str, Any] = copy.deepcopy(VANILLA_SECTIONS_IN)
        # extra fields
        extra_stuff["project"]["nickname"] = "the best python package around"
        extra_stuff["project"]["grocery_list"] = ["apple", "banana", "pumpkin"]
        # extra sections
        extra_stuff["baz"] = {"a": 11}
        extra_stuff["foo"] = {"bar": {"b": 22}}
        tomlkit.dump(extra_stuff, f)

    pyproject_toml_expected = {
        **BUILD_SYSTEM_SECTION,
        "project": {
            "nickname": "the best python package around",
            "grocery_list": ["apple", "banana", "pumpkin"],
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS_OUT,
            "keywords": [
                "python",
                "REST",
                "tools",
                "utilities",
                "OpenTelemetry",
                "tracing",
                "telemetry",
            ],
            "classifiers": [
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
            ],
            **PYPI_URLS_KEYVALS,
        },
        "tool": {
            "setuptools_scm": {},
            "setuptools": {
                "package-data": {"*": ["py.typed"]},
                "packages": {"find": {"exclude": EXCLUDE_DIRS, "namespaces": False}},
            },
        },
        # the extra sections
        "baz": extra_stuff["baz"],
        "foo": extra_stuff["foo"],
    }

    # run pyproject_toml_builder
    pyproject_toml_builder.work(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


# NOTE: test 50 was removed -- it tested deprecated functionality


def test_60_defined_project_version__error(directory: Path, requests_mock: Any) -> None:
    """Test situation where 'project.version' is defined."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = directory / "pyproject.toml"

    gha_input = pyproject_toml_builder.GHAInput(
        auto_mypy_option=False,
        python_min=(3, 6),
    )

    # write the original pyproject.toml
    input = copy.deepcopy(VANILLA_SECTIONS_IN)
    input["project"]["version"] = "1.2.3"
    with open(pyproject_toml_path, "w") as f:
        tomlkit.dump(input, f)

    # run pyproject_toml_builder
    with pytest.raises(
        Exception,
        match=re.escape("pyproject.toml must NOT define 'project.version'"),
    ):
        pyproject_toml_builder.work(
            pyproject_toml_path,
            GITHUB_FULL_REPO,
            TOKEN,
            gha_input,
        )


def test_70_defined_init_version__error(directory: Path, requests_mock: Any) -> None:
    """Test situation where 'project.version' is defined."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = directory / "pyproject.toml"

    gha_input = pyproject_toml_builder.GHAInput(
        auto_mypy_option=False,
        python_min=(3, 6),
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        tomlkit.dump(VANILLA_SECTIONS_IN, f)

    # write the illegal __version__
    with open(directory / "mock_package/__init__.py", "w") as f:
        f.write("__version__ = '1.2.3'")

    # run pyproject_toml_builder
    with pytest.raises(
        Exception,
        match=re.escape("pyproject.toml must NOT define 'project.version'"),
    ):
        pyproject_toml_builder.work(
            pyproject_toml_path,
            GITHUB_FULL_REPO,
            TOKEN,
            gha_input,
        )


def test_80_auto_mypy_option(directory: Path, requests_mock: Any) -> None:
    """Test using auto_mypy_option."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = directory / "pyproject.toml"

    gha_input = pyproject_toml_builder.GHAInput(
        python_min=(3, 6),
        auto_mypy_option=True,
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        tomlkit.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        **BUILD_SYSTEM_SECTION,
        "project": {
            "name": "mock-package",
            **NO_PYPI_VANILLA_PROJECT_KEYVALS_OUT,  # the true minimum is more vanilla than vanilla)
            **{
                "optional-dependencies": {
                    **NO_PYPI_VANILLA_PROJECT_KEYVALS_OUT["optional-dependencies"],  # type: ignore[dict-item]
                    **{
                        "mypy": sorted(["wipac-telemetry", "pen", "paper", "hard-work"])
                    },
                }
            },
        },
        "tool": {
            "setuptools_scm": {},
            "setuptools": {
                "package-data": {"*": ["py.typed"]},
                "packages": {"find": {"exclude": EXCLUDE_DIRS, "namespaces": False}},
            },
        },
    }

    # run pyproject_toml_builder
    pyproject_toml_builder.work(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)
