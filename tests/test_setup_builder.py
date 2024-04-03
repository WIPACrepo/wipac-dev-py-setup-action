"""Test pyproject_toml_builder.py"""

import copy
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import dotty_dict
import pytest
import toml

# pylint:disable=redefined-outer-name,invalid-name
# docfmt: skip-file-ric-evans

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
DIRECTORY_EXCLUDE = [
    "test",
    "tests",
    "doc",
    "docs",
    "resource",
    "resources",
    "example",
    "examples",
]
LICENSE = "MIT"
TOKEN = "token"

NONBUMPING_COMMIT_MESSAGE = "foo bar baz"


#
# VANILLA SECTIONS
#


VANILLA_SECTIONS_IN = {
    "project": {
        "version": "1.2.3",
        "dependencies": [
            "pyjwt",
            "requests",
            "requests-futures",
            "tornado",
            "wipac-dev-tools",
        ],
    },
    "project.optional-dependencies": {
        "telemetry": [
            "wipac-telemetry",
        ]
    },
}

VANILLA_SECTIONS_OUT = {
    "build-system": {
        "requires": ["setuptools>=61.0"],
        "build-backend": "setuptools.build_meta",
    },
    "project.optional-dependencies": {
        "telemetry": [
            "wipac-telemetry",
        ]
    },
    "project.urls": {
        "Homepage": "https://pypi.org/project/wipac-mock-package/",
        "Tracker": "https://github.com/foobarbaz-org/foobarbaz-repo/issues",
        "Source": "https://github.com/foobarbaz-org/foobarbaz-repo",
    },
}

# allow patch releases without specified commit tags (patch_without_tag=True)
PATCH_WITHOUT_TAG_WORKAROUND = [
    chr(i)
    for i in range(32, 127)
    if chr(i) not in ['"', ","]  # else upsets toml syntax
]

VANILLA_PROJECT_KEYVALS = {
    "version": "1.2.3",
    "url": "https://github.com/foobarbaz-org/foobarbaz-repo",
    "author": AUTHOR,
    "author_email": AUTHOR_EMAIL,
    "description": "Ceci n’est pas une pipe",
    "readme": "README.md",
    "license": "MIT",
    "requires-python": ">=3.6, <3.12",
    "find": {"namespaces": False},
    "dependencies": [
        "pyjwt",
        "requests",
        "requests-futures",
        "tornado",
        "wipac-dev-tools",
    ],
}

VANILLA_SEMANTIC_RELEASE_SECTIONS = {
    "tool.semantic_release": {
        "version_toml": ["pyproject.toml:project.version"],
        "commit_parser": "emoji",
        "commit_parser_options": {
            "major_tags": ["[major]"],
            "minor_tags": ["[minor]", "[feature]"],
            "patch_tags": ["[patch]", "[fix]"] + sorted(PATCH_WITHOUT_TAG_WORKAROUND),
        },
    }
}

SEMANTIC_RELEASE_SECTIONS_NO_PATCH = copy.deepcopy(VANILLA_SEMANTIC_RELEASE_SECTIONS)
for entry in PATCH_WITHOUT_TAG_WORKAROUND:
    SEMANTIC_RELEASE_SECTIONS_NO_PATCH["tool.semantic_release"][
        "commit_parser_options"
    ]["patch_tags"].remove(entry)
assert VANILLA_SEMANTIC_RELEASE_SECTIONS != SEMANTIC_RELEASE_SECTIONS_NO_PATCH

VANILLA_PACKAGE_DATA_SECTION = {
    "tool.setuptools.package-data": {
        "*": ["py.typed"],
    },
}

VANILLA_FIND_EXCLUDE_KEYVAL = {"exclude": DIRECTORY_EXCLUDE}


################################################################################
# HELPER FUNCTIONS
################################################################################


def assert_outputted_pyproject_toml(
    pyproject_toml_path: Path, expected: dict[str, Any]
) -> None:
    """Compare each's contents casted to a dict."""
    print()
    print("EXPECTED TOML OUTPUT:")
    print(expected)

    print()
    print("ACTUAL TOML OUTPUT:")
    with open(pyproject_toml_path) as f:
        actual = toml.load(f)
        print(actual)

    print()
    # resolve dotted keys for comparison
    assert dotty_dict.dotty(expected).to_dict() == dotty_dict.dotty(actual).to_dict()


################################################################################
# FIXTURES
################################################################################


def _directory(version: str) -> str:
    _dir = f"test-dir-{uuid.uuid1()}"

    os.mkdir(_dir)
    with open(f"{_dir}/README.md", "w") as f:
        f.write("# This is a test package, it's not real\n")

    os.mkdir(f"{_dir}/mock_package")
    with open(f"{_dir}/mock_package/__init__.py", "w") as f:
        f.write(f"__version__ = '{version}'\n")

    os.mkdir(f"{_dir}/.circleci")
    Path(f"{_dir}/.circleci/config.yml").touch()

    print(_dir)
    return _dir


@pytest.fixture
def directory() -> str:
    """Get path to pyproject.toml in a random testing directory."""
    return _directory("1.2.3")


@pytest.fixture
def directory_0_0_0() -> str:
    """Get path to pyproject.toml in a random testing directory."""
    return _directory("0.0.0")


@pytest.fixture
def directory_0_0_Z() -> str:
    """Get path to pyproject.toml in a random testing directory."""
    return _directory("0.0.42")


@pytest.fixture
def directory_0_Y_Z() -> str:
    """Get path to pyproject.toml in a random testing directory."""
    return _directory("0.45.6")


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


def test_00_minimum_input(directory: str, requests_mock: Any) -> None:
    """Test using bare minimum input."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = Path(f"{directory}/pyproject.toml")

    gha_input = pyproject_toml_builder.GHAInput(
        python_min=(3, 6),
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        toml.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        "project": {  # generated by WIPACrepo/wipac-dev-py-setup-action: name, version
            "name": "mock-package",
            **VANILLA_PROJECT_KEYVALS,
        },
        **VANILLA_SEMANTIC_RELEASE_SECTIONS,
        **VANILLA_SECTIONS_OUT,
        **VANILLA_PACKAGE_DATA_SECTION,
        "tool.setuptools.packages.find": {  # generated by WIPACrepo/wipac-dev-py-setup-action: include/exclude
            **VANILLA_FIND_EXCLUDE_KEYVAL,
        },
    }

    # run pyproject_toml_builder
    pyproject_toml_builder.main(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_01_minimum_input_w_pypi(directory: str, requests_mock: Any) -> None:
    """Test using the minimum input with pypi attrs."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = Path(f"{directory}/pyproject.toml")

    gha_input = pyproject_toml_builder.GHAInput(
        pypi_name="wipac-mock-package",
        python_min=(3, 6),
        keywords=["WIPAC", "IceCube"],
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
    )

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        toml.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        "project": {  # generated by WIPACrepo/wipac-dev-py-setup-action: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS,
            "keywords": ["WIPAC", "IceCube"],
            "classifiers": [
                "Development Status :: 5 - Production/Stable",
                "License :: OSI Approved :: MIT License",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
            ],
        },
        **VANILLA_SEMANTIC_RELEASE_SECTIONS,
        **VANILLA_SECTIONS_OUT,
        **VANILLA_PACKAGE_DATA_SECTION,
        "tool.setuptools.packages.find": {  # generated by WIPACrepo/wipac-dev-py-setup-action: include/exclude
            **VANILLA_FIND_EXCLUDE_KEYVAL,
        },
    }

    # run pyproject_toml_builder
    pyproject_toml_builder.main(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_10_keywords(directory: str, requests_mock: Any) -> None:
    """Test using  `keywords`."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = Path(f"{directory}/pyproject.toml")

    gha_input = pyproject_toml_builder.GHAInput(
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
        toml.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        "project": {  # generated by WIPACrepo/wipac-dev-py-setup-action: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS,
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
                "WIPAC",
                "IceCube",
            ],
            "classifiers": [
                "Development Status :: 5 - Production/Stable",
                "License :: OSI Approved :: MIT License",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
            ],
        },
        **VANILLA_SEMANTIC_RELEASE_SECTIONS,
        **VANILLA_SECTIONS_OUT,
        **VANILLA_PACKAGE_DATA_SECTION,
        "tool.setuptools.packages.find": {  # generated by WIPACrepo/wipac-dev-py-setup-action: include/exclude
            **VANILLA_FIND_EXCLUDE_KEYVAL,
        },
    }

    # run pyproject_toml_builder
    pyproject_toml_builder.main(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_20_python_max(directory: str, requests_mock: Any) -> None:
    """Test using  `python_max`."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = Path(f"{directory}/pyproject.toml")

    gha_input = pyproject_toml_builder.GHAInput(
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
        toml.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        "project": {  # generated by WIPACrepo/wipac-dev-py-setup-action: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS,
            "keywords": [
                "python",
                "REST",
                "tools",
                "utilities",
                "OpenTelemetry",
                "tracing",
                "telemetry",
                "WIPAC",
                "IceCube",
            ],
            "classifiers": [
                "Development Status :: 5 - Production/Stable",
                "License :: OSI Approved :: MIT License",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
            ],
        },
        **VANILLA_SEMANTIC_RELEASE_SECTIONS,
        "options": {  # generated by WIPACrepo/wipac-dev-py-setup-action: requires-python, packages
            "install_requires": [
                "pyjwt",
                "requests",
                "requests-futures",
                "tornado",
                "wipac-dev-tools",
            ],
            "requires-python": ">=3.6, <3.10",
            "packages": "find:",
        },
        "options.extras_require": {
            "telemetry": ["wipac-telemetry"],
        },
        **VANILLA_PACKAGE_DATA_SECTION,
        "tool.setuptools.packages.find": {  # generated by WIPACrepo/wipac-dev-py-setup-action: include/exclude
            **VANILLA_FIND_EXCLUDE_KEYVAL,
        },
    }

    # run pyproject_toml_builder
    pyproject_toml_builder.main(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_30_package_dirs__single(directory: str, requests_mock: Any) -> None:
    """Test using  `package_dirs` & a single desired package."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = Path(f"{directory}/pyproject.toml")

    gha_input = pyproject_toml_builder.GHAInput(
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
        toml.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        "project": {  # generated by WIPACrepo/wipac-dev-py-setup-action: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS,
            "keywords": [
                "python",
                "REST",
                "tools",
                "utilities",
                "OpenTelemetry",
                "tracing",
                "telemetry",
                "WIPAC",
                "IceCube",
            ],
            "classifiers": [
                "Development Status :: 5 - Production/Stable",
                "License :: OSI Approved :: MIT License",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
            ],
        },
        **VANILLA_SEMANTIC_RELEASE_SECTIONS,
        **VANILLA_SECTIONS_OUT,
        **VANILLA_PACKAGE_DATA_SECTION,
        "tool.setuptools.packages.find": {  # generated by WIPACrepo/wipac-dev-py-setup-action: include/exclude
            "include": ["mock_package", "mock_package.*"],
            **VANILLA_FIND_EXCLUDE_KEYVAL,
        },
    }

    # make an extra package *not* to be included
    os.mkdir(f"{directory}/mock_package_test")
    Path(f"{directory}/mock_package_test/__init__.py").touch()

    # run pyproject_toml_builder
    pyproject_toml_builder.main(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_34_package_dirs__multi_autoname(directory: str, requests_mock: Any) -> None:
    """Test using  `package_dirs` & multiple desired packages."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = Path(f"{directory}/pyproject.toml")

    gha_input = pyproject_toml_builder.GHAInput(
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
        toml.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        "project": {  # generated by WIPACrepo/wipac-dev-py-setup-action: name, version, author, author_email, keywords
            "name": "mock-package-another-one",
            **VANILLA_PROJECT_KEYVALS,
            "keywords": [
                "python",
                "REST",
                "tools",
                "utilities",
                "OpenTelemetry",
                "tracing",
                "telemetry",
                "WIPAC",
                "IceCube",
            ],
        },
        **VANILLA_SEMANTIC_RELEASE_SECTIONS,
        **VANILLA_SECTIONS_OUT,
        **VANILLA_PACKAGE_DATA_SECTION,
        "tool.setuptools.packages.find": {  # generated by WIPACrepo/wipac-dev-py-setup-action: include/exclude
            "include": [
                "mock_package",
                "another_one",
                "mock_package.*",
                "another_one.*",
            ],
            **VANILLA_FIND_EXCLUDE_KEYVAL,
        },
    }

    # make an extra package *not* to be included
    os.mkdir(f"{directory}/mock_package_test")
    Path(f"{directory}/mock_package_test/__init__.py").touch()

    # make an extra package *TO BE* included
    os.mkdir(f"{directory}/another_one")
    Path(f"{directory}/another_one/__init__.py").touch()
    with open(f"{directory}/another_one/__init__.py", "w") as f:
        f.write("__version__ = '1.2.3'\n")

    # run pyproject_toml_builder
    pyproject_toml_builder.main(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_35_package_dirs__multi(directory: str, requests_mock: Any) -> None:
    """Test using  `package_dirs` & multiple desired packages."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = Path(f"{directory}/pyproject.toml")

    gha_input = pyproject_toml_builder.GHAInput(
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
        toml.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        "project": {  # generated by WIPACrepo/wipac-dev-py-setup-action: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS,
            "keywords": [
                "python",
                "REST",
                "tools",
                "utilities",
                "OpenTelemetry",
                "tracing",
                "telemetry",
                "WIPAC",
                "IceCube",
            ],
            "classifiers": [
                "Development Status :: 5 - Production/Stable",
                "License :: OSI Approved :: MIT License",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
            ],
        },
        **VANILLA_SEMANTIC_RELEASE_SECTIONS,
        **VANILLA_SECTIONS_OUT,
        **VANILLA_PACKAGE_DATA_SECTION,
        "tool.setuptools.packages.find": {  # generated by WIPACrepo/wipac-dev-py-setup-action: include/exclude
            "include": [
                "mock_package",
                "another_one",
                "mock_package.*",
                "another_one.*",
            ],
            **VANILLA_FIND_EXCLUDE_KEYVAL,
        },
    }

    # make an extra package *not* to be included
    os.mkdir(f"{directory}/mock_package_test")
    Path(f"{directory}/mock_package_test/__init__.py").touch()

    # make an extra package *TO BE* included
    os.mkdir(f"{directory}/another_one")
    Path(f"{directory}/another_one/__init__.py").touch()
    with open(f"{directory}/another_one/__init__.py", "w") as f:
        f.write("__version__ = '1.2.3'\n")

    # run pyproject_toml_builder
    pyproject_toml_builder.main(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


def test_36_package_dirs__multi_missing_init__error(
    directory: str, requests_mock: Any
) -> None:
    """Test using  `package_dirs` & multiple desired packages."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = Path(f"{directory}/pyproject.toml")

    gha_input = pyproject_toml_builder.GHAInput(
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
        toml.dump(VANILLA_SECTIONS_IN, f)

    # make an extra package *not* to be included
    os.mkdir(f"{directory}/mock_package_test")
    Path(f"{directory}/mock_package_test/__init__.py").touch()

    # make an extra package *TO BE* included
    os.mkdir(f"{directory}/another_one")

    # run pyproject_toml_builder
    with pytest.raises(
        Exception,
        match=r"Package directory not found: another_one \(defined in setup\.cfg\)\. Is the directory missing an __init__\.py\?",
    ):
        pyproject_toml_builder.main(
            pyproject_toml_path,
            GITHUB_FULL_REPO,
            TOKEN,
            NONBUMPING_COMMIT_MESSAGE,
            gha_input,
        )


def test_37_package_dirs__multi_missing_version__error(
    directory: str, requests_mock: Any
) -> None:
    """Test using  `package_dirs` & multiple desired packages."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = Path(f"{directory}/pyproject.toml")

    gha_input = pyproject_toml_builder.GHAInput(
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
        toml.dump(VANILLA_SECTIONS_IN, f)

    # make an extra package *not* to be included
    os.mkdir(f"{directory}/mock_package_test")
    Path(f"{directory}/mock_package_test/__init__.py").touch()

    # make an extra package *TO BE* included
    os.mkdir(f"{directory}/another_one")
    Path(f"{directory}/another_one/__init__.py").touch()

    # run pyproject_toml_builder
    with pytest.raises(
        Exception,
        match=r"Cannot find __version__ in .*/another_one/__init__\.py",
    ):
        pyproject_toml_builder.main(
            pyproject_toml_path,
            GITHUB_FULL_REPO,
            TOKEN,
            NONBUMPING_COMMIT_MESSAGE,
            gha_input,
        )


def test_38_package_dirs__multi_mismatch_version__error(
    directory: str, requests_mock: Any
) -> None:
    """Test using  `package_dirs` & multiple desired packages."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = Path(f"{directory}/pyproject.toml")

    gha_input = pyproject_toml_builder.GHAInput(
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
        toml.dump(VANILLA_SECTIONS_IN, f)

    # make an extra package *not* to be included
    os.mkdir(f"{directory}/mock_package_test")
    Path(f"{directory}/mock_package_test/__init__.py").touch()

    # make an extra package *TO BE* included
    os.mkdir(f"{directory}/another_one")
    Path(f"{directory}/another_one/__init__.py").touch()
    with open(f"{directory}/another_one/__init__.py", "w") as f:
        f.write("__version__ = '3.4.5'\n")

    # run pyproject_toml_builder
    with pytest.raises(Exception, match=r"Version mismatch between packages*"):
        pyproject_toml_builder.main(
            pyproject_toml_path,
            GITHUB_FULL_REPO,
            TOKEN,
            NONBUMPING_COMMIT_MESSAGE,
            gha_input,
        )


def test_40_extra_fields(directory: str, requests_mock: Any) -> None:
    """Test using  extra stuff in "options":{ & "project":{."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = Path(f"{directory}/pyproject.toml")

    gha_input = pyproject_toml_builder.GHAInput(
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
        toml.dump(
            {
                "project": {
                    "nickname": "the best python package around",
                    "grocery_list": ["apple", "banana", "pumpkin"],
                },
                "options": {
                    "install_requires": [
                        "pyjwt",
                        "requests",
                        "requests-futures",
                        "tornado",
                        "wipac-dev-tools",
                    ],
                    "heres_an_obviously_extra_field": "it's very obvious, isn't it",
                    "foo_bar_baz_foo_bar_baz_foo_bar_baz": ["foo!", "bar!", "baz!"],
                },
                "options.extras_require": {
                    "telemetry": ["wipac-telemetry"],
                },
            },
            f,
        )

    pyproject_toml_expected = {
        "project": {  # generated by WIPACrepo/wipac-dev-py-setup-action: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
            "nickname": "the best python package around",
            "grocery_list": ["apple", "banana", "pumpkin"],
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS,
            "keywords": [
                "python",
                "REST",
                "tools",
                "utilities",
                "OpenTelemetry",
                "tracing",
                "telemetry",
                "WIPAC",
                "IceCube",
            ],
            "classifiers": [
                "Development Status :: 5 - Production/Stable",
                "License :: OSI Approved :: MIT License",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
            ],
        },
        **VANILLA_SEMANTIC_RELEASE_SECTIONS,
        "options": {  # generated by WIPACrepo/wipac-dev-py-setup-action: requires-python, packages
            "install_requires": [
                "pyjwt",
                "requests",
                "requests-futures",
                "tornado",
                "wipac-dev-tools",
            ],
            "heres_an_obviously_extra_field": "it's very obvious, isn't it",
            "foo_bar_baz_foo_bar_baz_foo_bar_baz": [
                "foo!",
                "bar!",
                "baz!",
            ],
            "requires-python": ">=3.6, <3.12",
            "packages": "find:",
        },
        "options.extras_require": {
            "telemetry": ["wipac-telemetry"],
            **VANILLA_PACKAGE_DATA_SECTION,
            "tool.setuptools.packages.find": {  # generated by WIPACrepo/wipac-dev-py-setup-action: include/exclude
                **VANILLA_FIND_EXCLUDE_KEYVAL,
            },
        },
    }

    # run pyproject_toml_builder
    pyproject_toml_builder.main(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)


CLASSIFIER_0_0_0 = "Development Status :: 2 - Pre-Alpha"
CLASSIFIER_0_0_Z = "Development Status :: 3 - Alpha"
CLASSIFIER_0_Y_Z = "Development Status :: 4 - Beta"
CLASSIFIER_X_Y_Z = "Development Status :: 5 - Production/Stable"


@pytest.mark.parametrize(
    "commit_message,version,patch_without_tag,classifier",
    [
        #
        # no embedded tag
        ("add the thing", "0.0.0", False, CLASSIFIER_0_0_0),
        ("add the thing", "0.0.0", True, CLASSIFIER_0_0_Z),
        #
        ("add the thing", "0.0.Z", False, CLASSIFIER_0_0_Z),
        ("add the thing", "0.0.Z", True, CLASSIFIER_0_0_Z),
        #
        ("add the thing", "0.Y.Z", False, CLASSIFIER_0_Y_Z),
        ("add the thing", "0.Y.Z", True, CLASSIFIER_0_Y_Z),
        #
        # FIX
        ("Bug [fix]", "0.0.0", False, CLASSIFIER_0_0_Z),
        ("Bug [fix]", "0.0.0", True, CLASSIFIER_0_0_Z),
        #
        ("Bug [fix]", "0.0.Z", False, CLASSIFIER_0_0_Z),
        ("Bug [fix]", "0.0.Z", True, CLASSIFIER_0_0_Z),
        #
        ("Bug [fix]", "0.Y.Z", False, CLASSIFIER_0_Y_Z),
        ("Bug [fix]", "0.Y.Z", True, CLASSIFIER_0_Y_Z),
        #
        # PATCH
        ("Bug Pt-2 [patch]", "0.0.0", False, CLASSIFIER_0_0_Z),
        ("Bug Pt-2 [patch]", "0.0.0", True, CLASSIFIER_0_0_Z),
        #
        ("Bug Pt-2 [patch]", "0.0.Z", False, CLASSIFIER_0_0_Z),
        ("Bug Pt-2 [patch]", "0.0.Z", True, CLASSIFIER_0_0_Z),
        #
        ("Bug Pt-2 [patch]", "0.Y.Z", False, CLASSIFIER_0_Y_Z),
        ("Bug Pt-2 [patch]", "0.Y.Z", True, CLASSIFIER_0_Y_Z),
        #
        # MINOR
        ("New Feature [minor]", "0.0.0", False, CLASSIFIER_0_Y_Z),
        ("New Feature [minor]", "0.0.0", True, CLASSIFIER_0_Y_Z),
        #
        ("New Feature [minor]", "0.0.Z", False, CLASSIFIER_0_Y_Z),
        ("New Feature [minor]", "0.0.Z", True, CLASSIFIER_0_Y_Z),
        #
        ("New Feature [minor]", "0.Y.Z", False, CLASSIFIER_0_Y_Z),
        ("New Feature [minor]", "0.Y.Z", True, CLASSIFIER_0_Y_Z),
        #
        # MAJOR
        ("Big Change [major]", "0.0.0", False, CLASSIFIER_X_Y_Z),
        ("Big Change [major]", "0.0.0", True, CLASSIFIER_X_Y_Z),
        #
        ("Big Change [major]", "0.0.Z", False, CLASSIFIER_X_Y_Z),
        ("Big Change [major]", "0.0.Z", True, CLASSIFIER_X_Y_Z),
        #
        ("Big Change [major]", "0.Y.Z", False, CLASSIFIER_X_Y_Z),
        ("Big Change [major]", "0.Y.Z", True, CLASSIFIER_X_Y_Z),
    ],
)
def test_50_bumping(
    version: str,
    commit_message: str,
    patch_without_tag: bool,
    classifier: str,
    requests_mock: Any,
) -> None:
    """Test bumping configurations ."""
    mock_many_requests(requests_mock)

    pyproject_toml_path = Path(f"{_directory(version)}/pyproject.toml")

    gha_input = pyproject_toml_builder.GHAInput(
        pypi_name="wipac-mock-package",
        python_min=(3, 6),
        keywords=["WIPAC", "IceCube"],
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
    )
    if not patch_without_tag:
        gha_input.patch_without_tag = False

    # write the original pyproject.toml
    with open(pyproject_toml_path, "w") as f:
        toml.dump(VANILLA_SECTIONS_IN, f)

    pyproject_toml_expected = {
        "project": {  # generated by WIPACrepo/wipac-dev-py-setup-action: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
            "name": "wipac-mock-package",
            **VANILLA_PROJECT_KEYVALS,
            "keywords": ["WIPAC", "IceCube"],
            "classifiers": [
                classifier,
                "License :: OSI Approved :: MIT License",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
            ],
        },
        **{
            k: v
            for k, v in (
                VANILLA_SEMANTIC_RELEASE_SECTIONS
                if patch_without_tag
                else SEMANTIC_RELEASE_SECTIONS_NO_PATCH
            )
        },
        **VANILLA_SECTIONS_OUT,
        **VANILLA_PACKAGE_DATA_SECTION,
        "tool.setuptools.packages.find": {  # generated by WIPACrepo/wipac-dev-py-setup-action: include/exclude
            **VANILLA_FIND_EXCLUDE_KEYVAL,
        },
    }

    # run pyproject_toml_builder
    pyproject_toml_builder.main(
        pyproject_toml_path,
        GITHUB_FULL_REPO,
        TOKEN,
        commit_message,
        gha_input,
    )

    # assert outputted pyproject.toml
    assert_outputted_pyproject_toml(pyproject_toml_path, pyproject_toml_expected)
