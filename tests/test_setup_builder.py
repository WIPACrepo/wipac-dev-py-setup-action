"""Test setup_builder.py"""

# pylint:disable=redefined-outer-name
# docfmt: skip-file-ric-evans

import os
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

sys.path.append(".")
import setup_builder  # noqa: E402 # isort:skip # pylint:disable=import-error,wrong-import-position


GITHUB_FULL_REPO = "foobarbaz-org/foobarbaz-repo"
AUTHOR = "WIPAC Developers"
AUTHOR_EMAIL = "developers@icecube.wisc.edu"
BASE_KEYWORDS = ["WIPAC", "IceCube"]
DIRECTORY_EXCLUDE = ["test", "tests", "doc", "docs", "resource", "resources"]
LICENSE = "MIT"
TOKEN = "token"

NONBUMPING_COMMIT_MESSAGE = "foo bar baz"


def assert_outputted_setup_cfg(setup_cfg_path: Path, setup_cfg_out: str) -> None:
    with open(setup_cfg_path) as f:
        print("EXPECTED:")
        print(setup_cfg_out + "\n")
        expected = setup_cfg_out.replace("    ", "\t").split("\n")
        actual = list(f.readlines())
        print("ACTUAL:")
        for actual_line in actual:
            print(actual_line, end="")
        print("- " * 20)
        for i, actual_line in enumerate(actual):
            assert actual_line == expected[i] + "\n"


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
    Path(f"{_dir}/.circleci/config.yml").touch()

    print(_dir)
    return _dir


def test_00_minimum_section(directory: str, requests_mock: Any) -> None:
    """Test using a minimum [wipac:cicd_setup_builder]."""
    setup_cfg_path = Path(f"{directory}/setup.cfg")

    cicd_setup_builder = f"""[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
"""

    setup_cfg_in = f"""{cicd_setup_builder}
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

    setup_cfg_out = f"""{cicd_setup_builder}
[metadata]  # generated by wipac:cicd_setup_builder: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
name = wipac-mock-package
version = attr: mock_package.__version__
url = https://github.com/foobarbaz-org/foobarbaz-repo
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
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

[semantic_release]  # fully-generated by wipac:cicd_setup_builder
version_variable = mock_package/__init__.py:__version__
upload_to_pypi = True
patch_without_tag = True
commit_parser = semantic_release.history.emoji_parser
major_emoji = [major]
minor_emoji = [minor]
patch_emoji = [fix], [patch]
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

[options.extras_require]
telemetry =
    wipac-telemetry

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

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    # write the original setup.cfg
    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    # mock the outgoing requests
    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    # run setup_builder
    setup_builder.main(
        setup_cfg_path,
        GITHUB_FULL_REPO,
        BASE_KEYWORDS,
        DIRECTORY_EXCLUDE,
        LICENSE,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
    )

    # assert outputted setup.cfg
    assert_outputted_setup_cfg(setup_cfg_path, setup_cfg_out)


def test_01_minimum_section_no_pypi(directory: str, requests_mock: Any) -> None:
    """Test using a minimum [wipac:cicd_setup_builder] without PyPI attributes."""
    setup_cfg_path = Path(f"{directory}/setup.cfg")

    cicd_setup_builder = f"""[wipac:cicd_setup_builder]
python_min = 3.6
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
"""

    setup_cfg_in = f"""{cicd_setup_builder}
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

    setup_cfg_out = f"""{cicd_setup_builder}
[metadata]  # generated by wipac:cicd_setup_builder: version, author, author_email, keywords
version = attr: mock_package.__version__
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
keywords =
    WIPAC
    IceCube

[semantic_release]  # fully-generated by wipac:cicd_setup_builder
version_variable = mock_package/__init__.py:__version__
upload_to_pypi = False
patch_without_tag = True
commit_parser = semantic_release.history.emoji_parser
major_emoji = [major]
minor_emoji = [minor]
patch_emoji = [fix], [patch]
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

[options.extras_require]
telemetry =
    wipac-telemetry

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

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    # write the original setup.cfg
    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    # mock the outgoing requests
    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    # run setup_builder
    setup_builder.main(
        setup_cfg_path,
        GITHUB_FULL_REPO,
        BASE_KEYWORDS,
        DIRECTORY_EXCLUDE,
        LICENSE,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
    )

    # assert outputted setup.cfg
    assert_outputted_setup_cfg(setup_cfg_path, setup_cfg_out)


def test_02_minimum_section_no_pypi_no_keywords_no_author(
    directory: str, requests_mock: Any
) -> None:
    """Test using a minimum [wipac:cicd_setup_builder] without PyPI attributes."""
    setup_cfg_path = Path(f"{directory}/setup.cfg")

    cicd_setup_builder = """[wipac:cicd_setup_builder]
python_min = 3.6
"""

    setup_cfg_in = f"""{cicd_setup_builder}
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
python_min = 3.6

[metadata]  # generated by wipac:cicd_setup_builder: version
version = attr: mock_package.__version__

[semantic_release]  # fully-generated by wipac:cicd_setup_builder
version_variable = mock_package/__init__.py:__version__
upload_to_pypi = False
patch_without_tag = True
commit_parser = semantic_release.history.emoji_parser
major_emoji = [major]
minor_emoji = [minor]
patch_emoji = [fix], [patch]
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

[options.extras_require]
telemetry =
    wipac-telemetry

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

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    # write the original setup.cfg
    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    # mock the outgoing requests
    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    # run setup_builder
    setup_builder.main(
        setup_cfg_path,
        GITHUB_FULL_REPO,
        [],
        DIRECTORY_EXCLUDE,
        LICENSE,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
    )

    # assert outputted setup.cfg
    assert_outputted_setup_cfg(setup_cfg_path, setup_cfg_out)


def test_10_keywords_spaced(directory: str, requests_mock: Any) -> None:
    """Test using [wipac:cicd_setup_builder] with `keywords_spaced`."""
    setup_cfg_path = Path(f"{directory}/setup.cfg")

    cicd_setup_builder = f"""[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
keywords_spaced = python REST tools "REST tools" utilities "OpenTelemetry" tracing telemetry "3+ word string keywords"
"""

    setup_cfg_in = f"""{cicd_setup_builder}
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

    setup_cfg_out = f"""{cicd_setup_builder}
[metadata]  # generated by wipac:cicd_setup_builder: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
name = wipac-mock-package
version = attr: mock_package.__version__
url = https://github.com/foobarbaz-org/foobarbaz-repo
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
description = Ceci n’est pas une pipe
long_description = file: README.md
long_description_content_type = text/markdown
keywords =
    python
    REST
    tools
    REST tools
    utilities
    OpenTelemetry
    tracing
    telemetry
    3+ word string keywords
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
commit_parser = semantic_release.history.emoji_parser
major_emoji = [major]
minor_emoji = [minor]
patch_emoji = [fix], [patch]
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

[options.extras_require]
telemetry =
    wipac-telemetry

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

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    # write the original setup.cfg
    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    # mock the outgoing requests
    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    # run setup_builder
    setup_builder.main(
        setup_cfg_path,
        GITHUB_FULL_REPO,
        BASE_KEYWORDS,
        DIRECTORY_EXCLUDE,
        LICENSE,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
    )

    # assert outputted setup.cfg
    assert_outputted_setup_cfg(setup_cfg_path, setup_cfg_out)


def test_20_python_max(directory: str, requests_mock: Any) -> None:
    """Test using [wipac:cicd_setup_builder] with `python_max`."""
    setup_cfg_path = Path(f"{directory}/setup.cfg")

    cicd_setup_builder = f"""[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6
python_max = 3.9
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
keywords_spaced = python REST tools utilities OpenTelemetry tracing telemetry
"""

    setup_cfg_in = f"""{cicd_setup_builder}
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

    setup_cfg_out = f"""{cicd_setup_builder}
[metadata]  # generated by wipac:cicd_setup_builder: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
name = wipac-mock-package
version = attr: mock_package.__version__
url = https://github.com/foobarbaz-org/foobarbaz-repo
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
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
download_url = https://pypi.org/project/wipac-mock-package/
project_urls =
    Tracker = https://github.com/foobarbaz-org/foobarbaz-repo/issues
    Source = https://github.com/foobarbaz-org/foobarbaz-repo

[semantic_release]  # fully-generated by wipac:cicd_setup_builder
version_variable = mock_package/__init__.py:__version__
upload_to_pypi = True
patch_without_tag = True
commit_parser = semantic_release.history.emoji_parser
major_emoji = [major]
minor_emoji = [minor]
patch_emoji = [fix], [patch]
branch = main

[options]  # generated by wipac:cicd_setup_builder: python_requires, packages
install_requires =
    pyjwt
    requests
    requests-futures
    tornado
    wipac-dev-tools
python_requires = >=3.6, <3.10
packages = find:

[options.extras_require]
telemetry =
    wipac-telemetry

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

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    # write the original setup.cfg
    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    # mock the outgoing requests
    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    # run setup_builder
    setup_builder.main(
        setup_cfg_path,
        GITHUB_FULL_REPO,
        BASE_KEYWORDS,
        DIRECTORY_EXCLUDE,
        LICENSE,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
    )

    # assert outputted setup.cfg
    assert_outputted_setup_cfg(setup_cfg_path, setup_cfg_out)


def test_30_package_dirs__single(directory: str, requests_mock: Any) -> None:
    """Test using [wipac:cicd_setup_builder] with `package_dirs` & a single desired package."""
    setup_cfg_path = Path(f"{directory}/setup.cfg")

    cicd_setup_builder = f"""[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
package_dirs = mock_package
keywords_spaced = python REST tools utilities OpenTelemetry tracing telemetry
"""

    setup_cfg_in = f"""{cicd_setup_builder}
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

    setup_cfg_out = f"""{cicd_setup_builder}
[metadata]  # generated by wipac:cicd_setup_builder: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
name = wipac-mock-package
version = attr: mock_package.__version__
url = https://github.com/foobarbaz-org/foobarbaz-repo
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
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

[semantic_release]  # fully-generated by wipac:cicd_setup_builder
version_variable = mock_package/__init__.py:__version__
upload_to_pypi = True
patch_without_tag = True
commit_parser = semantic_release.history.emoji_parser
major_emoji = [major]
minor_emoji = [minor]
patch_emoji = [fix], [patch]
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

[options.extras_require]
telemetry =
    wipac-telemetry

[options.package_data]  # generated by wipac:cicd_setup_builder: '*'
* = py.typed

[options.packages.find]  # generated by wipac:cicd_setup_builder: include/exclude
include =
    mock_package
    mock_package.*
exclude =
    test
    tests
    doc
    docs
    resource
    resources

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    # make an extra package *not* to be included
    os.mkdir(f"{directory}/mock_package_test")
    Path(f"{directory}/mock_package_test/__init__.py").touch()

    # write the original setup.cfg
    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    # mock the outgoing requests
    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    # run setup_builder
    setup_builder.main(
        setup_cfg_path,
        GITHUB_FULL_REPO,
        BASE_KEYWORDS,
        DIRECTORY_EXCLUDE,
        LICENSE,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
    )

    # assert outputted setup.cfg
    assert_outputted_setup_cfg(setup_cfg_path, setup_cfg_out)


def test_35_package_dirs__multi(directory: str, requests_mock: Any) -> None:
    """Test using [wipac:cicd_setup_builder] with `package_dirs` & multiple desired packages."""
    setup_cfg_path = Path(f"{directory}/setup.cfg")

    cicd_setup_builder = f"""[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
package_dirs =
    mock_package
    another_one
keywords_spaced = python REST tools utilities OpenTelemetry tracing telemetry
"""

    setup_cfg_in = f"""{cicd_setup_builder}
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

    setup_cfg_out = f"""{cicd_setup_builder}
[metadata]  # generated by wipac:cicd_setup_builder: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
name = wipac-mock-package
version = attr: mock_package.__version__
url = https://github.com/foobarbaz-org/foobarbaz-repo
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
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

[semantic_release]  # fully-generated by wipac:cicd_setup_builder
version_variable = mock_package/__init__.py:__version__,another_one/__init__.py:__version__
upload_to_pypi = True
patch_without_tag = True
commit_parser = semantic_release.history.emoji_parser
major_emoji = [major]
minor_emoji = [minor]
patch_emoji = [fix], [patch]
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

[options.extras_require]
telemetry =
    wipac-telemetry

[options.package_data]  # generated by wipac:cicd_setup_builder: '*'
* = py.typed

[options.packages.find]  # generated by wipac:cicd_setup_builder: include/exclude
include =
    mock_package
    another_one
    mock_package.*
    another_one.*
exclude =
    test
    tests
    doc
    docs
    resource
    resources

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    # make an extra package *not* to be included
    os.mkdir(f"{directory}/mock_package_test")
    Path(f"{directory}/mock_package_test/__init__.py").touch()

    # make an extra package *TO BE* included
    os.mkdir(f"{directory}/another_one")
    Path(f"{directory}/another_one/__init__.py").touch()
    with open(f"{directory}/another_one/__init__.py", "w") as f:
        f.write("__version__ = '1.2.3'\n")

    # write the original setup.cfg
    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    # mock the outgoing requests
    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    # run setup_builder
    setup_builder.main(
        setup_cfg_path,
        GITHUB_FULL_REPO,
        BASE_KEYWORDS,
        DIRECTORY_EXCLUDE,
        LICENSE,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
    )

    # assert outputted setup.cfg
    assert_outputted_setup_cfg(setup_cfg_path, setup_cfg_out)


def test_36_package_dirs__multi_missing_init__error(
    directory: str, requests_mock: Any
) -> None:
    """Test using [wipac:cicd_setup_builder] with `package_dirs` & multiple desired packages."""
    setup_cfg_path = Path(f"{directory}/setup.cfg")

    cicd_setup_builder = f"""[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
package_dirs =
    mock_package
    another_one
keywords_spaced = python REST tools utilities OpenTelemetry tracing telemetry
"""

    setup_cfg_in = f"""{cicd_setup_builder}
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

    # make an extra package *not* to be included
    os.mkdir(f"{directory}/mock_package_test")
    Path(f"{directory}/mock_package_test/__init__.py").touch()

    # make an extra package *TO BE* included
    os.mkdir(f"{directory}/another_one")

    # write the original setup.cfg
    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    # mock the outgoing requests
    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    # run setup_builder
    with pytest.raises(
        Exception,
        match=r"Package directory not found: another_one \(defined in setup\.cfg\)\. Is the directory missing an __init__\.py\?",
    ):
        setup_builder.main(
            setup_cfg_path,
            GITHUB_FULL_REPO,
            BASE_KEYWORDS,
            DIRECTORY_EXCLUDE,
            LICENSE,
            TOKEN,
        )


def test_37_package_dirs__multi_missing_version__error(
    directory: str, requests_mock: Any
) -> None:
    """Test using [wipac:cicd_setup_builder] with `package_dirs` & multiple desired packages."""
    setup_cfg_path = Path(f"{directory}/setup.cfg")

    cicd_setup_builder = f"""[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
package_dirs =
    mock_package
    another_one
keywords_spaced = python REST tools utilities OpenTelemetry tracing telemetry
"""

    setup_cfg_in = f"""{cicd_setup_builder}
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

    # make an extra package *not* to be included
    os.mkdir(f"{directory}/mock_package_test")
    Path(f"{directory}/mock_package_test/__init__.py").touch()

    # make an extra package *TO BE* included
    os.mkdir(f"{directory}/another_one")
    Path(f"{directory}/another_one/__init__.py").touch()

    # write the original setup.cfg
    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    # mock the outgoing requests
    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    # run setup_builder
    with pytest.raises(
        Exception,
        match=r"Cannot find __version__ in .*/another_one/__init__\.py",
    ):
        setup_builder.main(
            setup_cfg_path,
            GITHUB_FULL_REPO,
            BASE_KEYWORDS,
            DIRECTORY_EXCLUDE,
            LICENSE,
            TOKEN,
        )


def test_38_package_dirs__multi_mismatch_version__error(
    directory: str, requests_mock: Any
) -> None:
    """Test using [wipac:cicd_setup_builder] with `package_dirs` & multiple desired packages."""
    setup_cfg_path = Path(f"{directory}/setup.cfg")

    cicd_setup_builder = f"""[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
package_dirs =
    mock_package
    another_one
keywords_spaced = python REST tools utilities OpenTelemetry tracing telemetry
"""

    setup_cfg_in = f"""{cicd_setup_builder}
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

    # make an extra package *not* to be included
    os.mkdir(f"{directory}/mock_package_test")
    Path(f"{directory}/mock_package_test/__init__.py").touch()

    # make an extra package *TO BE* included
    os.mkdir(f"{directory}/another_one")
    Path(f"{directory}/another_one/__init__.py").touch()
    with open(f"{directory}/another_one/__init__.py", "w") as f:
        f.write("__version__ = '3.4.5'\n")

    # write the original setup.cfg
    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    # mock the outgoing requests
    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    # run setup_builder
    with pytest.raises(Exception, match=r"Version mismatch between packages*"):
        setup_builder.main(
            setup_cfg_path,
            GITHUB_FULL_REPO,
            BASE_KEYWORDS,
            DIRECTORY_EXCLUDE,
            LICENSE,
            TOKEN,
        )


def test_40_extra_fields(directory: str, requests_mock: Any) -> None:
    """Test using [wipac:cicd_setup_builder] with extra stuff in [options] & [metadata]."""
    setup_cfg_path = Path(f"{directory}/setup.cfg")

    cicd_setup_builder = f"""[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
keywords_spaced = python REST tools utilities OpenTelemetry tracing telemetry
"""

    setup_cfg_in = f"""{cicd_setup_builder}
[metadata]
nickname = the best python package around
grocery_list =
    apple
    banana
    pumpkin

[options]
install_requires =
    pyjwt
    requests
    requests-futures
    tornado
    wipac-dev-tools
heres_an_obviously_extra_field = it's very obvious, isn't it
foo_bar_baz_foo_bar_baz_foo_bar_baz =
    foo!
    bar!
    baz!

[options.extras_require]
telemetry =
    wipac-telemetry

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    setup_cfg_out = f"""[wipac:cicd_setup_builder]
pypi_name = wipac-mock-package
python_min = 3.6
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
keywords_spaced = python REST tools utilities OpenTelemetry tracing telemetry

[metadata]  # generated by wipac:cicd_setup_builder: name, version, url, author, author_email, description, long_description, long_description_content_type, keywords, license, classifiers, download_url, project_urls
nickname = the best python package around
grocery_list =
    apple
    banana
    pumpkin
name = wipac-mock-package
version = attr: mock_package.__version__
url = https://github.com/foobarbaz-org/foobarbaz-repo
author = {AUTHOR}
author_email = {AUTHOR_EMAIL}
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

[semantic_release]  # fully-generated by wipac:cicd_setup_builder
version_variable = mock_package/__init__.py:__version__
upload_to_pypi = True
patch_without_tag = True
commit_parser = semantic_release.history.emoji_parser
major_emoji = [major]
minor_emoji = [minor]
patch_emoji = [fix], [patch]
branch = main

[options]  # generated by wipac:cicd_setup_builder: python_requires, packages
install_requires =
    pyjwt
    requests
    requests-futures
    tornado
    wipac-dev-tools
heres_an_obviously_extra_field = it's very obvious, isn't it
foo_bar_baz_foo_bar_baz_foo_bar_baz =
    foo!
    bar!
    baz!
python_requires = >=3.6, <3.11
packages = find:

[options.extras_require]
telemetry =
    wipac-telemetry

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

[flake8]
ignore = E226,E231,E501

[tool:pytest]
flake8-ignore = E501 E231 E226
"""

    # write the original setup.cfg
    with open(setup_cfg_path, "w") as f:
        f.write(setup_cfg_in)

    # mock the outgoing requests
    requests_mock.get(
        f"https://api.github.com/repos/{GITHUB_FULL_REPO}",
        json={"default_branch": "main", "description": "Ceci n’est pas une pipe"},
    )
    requests_mock.get("https://docs.python.org/release/3.10.0/")
    requests_mock.get("https://docs.python.org/release/3.11.0/", status_code=404)

    # run setup_builder
    setup_builder.main(
        setup_cfg_path,
        GITHUB_FULL_REPO,
        BASE_KEYWORDS,
        DIRECTORY_EXCLUDE,
        LICENSE,
        TOKEN,
        NONBUMPING_COMMIT_MESSAGE,
    )

    # assert outputted setup.cfg
    assert_outputted_setup_cfg(setup_cfg_path, setup_cfg_out)
