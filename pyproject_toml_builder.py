"""Module to build `pyproject.toml` sections for use by `setup.py`/`setuptools`.

Used in CI/CD, used by GH Action.
"""

import argparse
import dataclasses
import itertools
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any, cast

import requests
import tomlkit
from tomlkit import TOMLDocument, array
from wipac_dev_tools import (
    argparse_tools,
    logging_tools,
    semver_parser_tools,
    strtobool,
)

from find_packages import iterate_dirnames

BUILDER_SECTION_NAME = "wipac:cicd_setup_builder"
GENERATED_STR = f"generated by {BUILDER_SECTION_NAME}"
REAMDE_BADGES_START_DELIMITER = "<!--- Top of README Badges (automated) --->"
REAMDE_BADGES_END_DELIMITER = "<!--- End of README Badges (automated) --->"

LOGGER = logging.getLogger("setup-builder")

SEMANTIC_RELEASE_MAJOR = ["[major]"]
SEMANTIC_RELEASE_MINOR = ["[minor]", "[feature]"]
SEMANTIC_RELEASE_PATCH = ["[patch]", "[fix]"]
PATCH_WITHOUT_TAG_WORKAROUND = [
    chr(i)
    for i in range(32, 127)
    if chr(i) not in ['"', ",", "\\"]  # else upsets toml syntax
]

DEV_STATUS_PREALPHA_0_0_0 = "Development Status :: 2 - Pre-Alpha"
DEV_STATUS_ALPHA_0_0_Z = "Development Status :: 3 - Alpha"
DEV_STATUS_BETA_0_Y_Z = "Development Status :: 4 - Beta"
DEV_STATUS_PROD_X_Y_Z = "Development Status :: 5 - Production/Stable"

# https://stackoverflow.com/a/71126828/13156561
DYNAMIC_DUNDER_VERSION = (
    "__version__ = importlib_metadata.version(__package__ or __name__)"
)

PythonMinMax = tuple[tuple[int, int], tuple[int, int]]


class GitHubAPI:
    """Relay info from the GitHub API."""

    def __init__(self, github_full_repo: str, oauth_token: str) -> None:
        self.url = f"https://github.com/{github_full_repo}"

        _headers = {"authorization": f"Bearer {oauth_token}"}
        _req = requests.get(
            f"https://api.github.com/repos/{github_full_repo}",
            headers=_headers,
        )
        _req.raise_for_status()
        _json = _req.json()
        self.default_branch = cast(str, _json["default_branch"])  # main/master/etc.
        self.description = cast(str, _json["description"])


@dataclasses.dataclass
class GHAInput:
    """The inputs passed from the client GitHub Action."""

    # REQUIRED
    python_min: tuple[int, int]

    # OPTIONAL (python)
    python_max: tuple[int, int] = dataclasses.field(
        default_factory=semver_parser_tools.get_latest_py3_release  # called only if no val
    )
    # OPTIONAL (packaging)
    package_dirs: list[str] = dataclasses.field(default_factory=list)
    exclude_dirs: list[str] = dataclasses.field(
        default_factory=lambda: [  # cannot use mutable type
            "test",
            "tests",
            "doc",
            "docs",
            "resource",
            "resources",
            "example",
            "examples",
        ]
    )
    # OPTIONAL (releases)
    pypi_name: str = ""
    patch_without_tag: bool = True
    # OPTIONAL (meta)
    keywords: list[str] = dataclasses.field(default_factory=list)
    author: str = ""
    author_email: str = ""

    auto_mypy_option: bool = False

    def __post_init__(self) -> None:
        # pypi-related metadata
        if self.pypi_name:
            if not self.keywords or not self.author or not self.author_email:
                raise Exception(
                    "'keywords', 'author', and 'author_email' must be provided when "
                    "'pypi_name' is `True`"
                )

        # validate python min/max
        for major, attr_name in [
            (self.python_min[0], "python_min"),
            (self.python_max[0], "python_max"),
        ]:
            if major < 3:
                raise Exception(
                    f"Python-release automation ('{attr_name}') does not work for python <3."
                )
            elif major >= 4:
                raise Exception(
                    f"Python-release automation ('{attr_name}') does not work for python 4+."
                )

    def get_requires_python(self) -> str:
        """Get a `[project]/python_requires` string from `self.python_range`.

        Ex: "">=3.6, <3.10" (cannot do "<=3.9" because 3.9.1 > 3.9)
        """
        return f">={self.python_min[0]}.{self.python_min[1]}, <{self.python_max[0]}.{self.python_max[1] + 1}"

    def python_classifiers(self) -> list[str]:
        """Get auto-detected `Programming Language :: Python :: *` list.

        NOTE: Will not work after the '3.* -> 4.0'-transition.
        """
        return [
            f"Programming Language :: Python :: 3.{r}"
            for r in range(self.python_min[1], self.python_max[1] + 1)
        ]


class FromFiles:
    """Get things that require reading files."""

    def __init__(
        self,
        root: Path,
        gha_input: GHAInput,
        commit_message: str,
    ) -> None:
        if not os.path.exists(root):
            raise NotADirectoryError(root)
        self.gha_input = gha_input
        self.root = root.resolve()
        self._pkg_paths = self._get_package_paths(self.gha_input.exclude_dirs)
        self.packages = [p.name for p in self._pkg_paths]
        self.readme_path = self._get_readme_path()

    def _get_package_paths(self, dirs_exclude: list[str]) -> list[Path]:
        """Find the package path(s)."""

        if not (available_pkgs := list(iterate_dirnames(self.root, dirs_exclude))):
            raise Exception(
                f"No package found in '{self.root}'. Are you missing an __init__.py?"
            )

        # check the pyproject.toml: package_dirs
        if self.gha_input.package_dirs:
            if not_ins := [
                p for p in self.gha_input.package_dirs if p not in available_pkgs
            ]:
                if len(not_ins) == 1:
                    raise Exception(
                        f"Package directory not found: "
                        f"{not_ins[0]} (defined in pyproject.toml). "
                        f"Is the directory missing an __init__.py?"
                    )
                raise Exception(
                    f"Package directories not found: "
                    f"{', '.join(not_ins)} (defined in pyproject.toml). "
                    f"Are the directories missing __init__.py files?"
                )

            return [self.root / p for p in self.gha_input.package_dirs]
        # use the auto-detected package (if there's ONE)
        else:
            if len(available_pkgs) > 1:
                raise Exception(
                    f"More than one package found in '{self.root}': {', '.join(available_pkgs)}. "
                    f"Either "
                    f"[1] list *all* your desired packages in your pyproject.toml's 'package_dirs', "
                    f"[2] remove the extra __init__.py file(s), "
                    f"or [3] list which packages to ignore in your GitHub Action step's 'with.exclude-dirs'."
                )
            return [self.root / available_pkgs[0]]

    def _get_readme_path(self) -> Path:
        """Return the 'README' file and its extension."""
        for fname in self.root.iterdir():
            if fname.stem == "README":
                return Path(fname)
        raise FileNotFoundError(f"No README file found in '{self.root}'")

    def get_dunder_version_inits(self, version_from_toml: str) -> list[str]:
        """Get the __init__.py file(s) that have a `__version__` string.

        Also, check if the retrieved `__version__` strings are equivalent.

        `__version__` needs to be parsed as plain text due to potential
        race condition, see:
        https://stackoverflow.com/a/2073599/13156561
        """

        def get_init_version(ppath: Path) -> tuple[Path, str | None]:
            with open(ppath / "__init__.py") as f:
                for line in f.readlines():
                    if line.startswith("__version__ ="):
                        # grab "X.Y.Z" from `__version__ = 'X.Y.Z'`
                        # or     foo() from `__version__ = foo()`
                        # - quote-style insensitive
                        if m := re.match(
                            r"^__version__ = [\"\'](?P<version>\w+\.\w+\.\w+)[\"\']",
                            line,
                        ):
                            return Path(f.name), m.group("version")
                        else:
                            raise Exception(
                                f"'__version__' must be in the semantic version format: "
                                f"{ppath.name}/__init__.py -> '{line.strip()}'"
                            )
                return Path(f.name), None

        fpath_versions = dict(get_init_version(p) for p in self._pkg_paths)
        fpath_versions = {k: v for k, v in fpath_versions.items() if v is not None}

        if init_versions := set(fpath_versions.values()):
            if len(init_versions) != 1:
                raise Exception(f"Version mismatch between packages: {fpath_versions}")
            if version_from_toml != list(init_versions)[0]:
                raise Exception(
                    f"Version mismatch between package(s) ({list(init_versions)[0]}) "
                    f"and pyproject.toml's 'project.version' ({version_from_toml})"
                )

        return [str(p.relative_to(self.root)) for p in fpath_versions.keys()]


def get_development_status(
    version: str,
    patch_without_tag: bool,
    commit_message: str,
) -> str:
    """Detect the development status from the package's version.

    Known Statuses (**not all are supported**):
        `"Development Status :: 1 - Planning"`
        `"Development Status :: 2 - Pre-Alpha"`
        `"Development Status :: 3 - Alpha"`
        `"Development Status :: 4 - Beta"`
        `"Development Status :: 5 - Production/Stable"`
        `"Development Status :: 6 - Mature"`
        `"Development Status :: 7 - Inactive"`
    """

    # detect version threshold crossing
    pending_major_bump = any(k in commit_message for k in SEMANTIC_RELEASE_MAJOR)
    pending_minor_bump = any(k in commit_message for k in SEMANTIC_RELEASE_MINOR)
    pending_patch_bump = patch_without_tag or any(
        k in commit_message for k in SEMANTIC_RELEASE_PATCH
    )

    # NOTE - if someday we abandon python-semantic-release, this is a starting place to detect the next version -- in this case, we'd change the version number before merging to main

    if version == "0.0.0":
        if pending_major_bump:
            return DEV_STATUS_PROD_X_Y_Z  # MAJOR-BUMPPING STRAIGHT TO PROD
        elif pending_minor_bump:
            return DEV_STATUS_BETA_0_Y_Z  # MINOR-BUMPPING STRAIGHT TO BETA
        elif pending_patch_bump:
            return DEV_STATUS_ALPHA_0_0_Z  # PATCH-BUMPPING STRAIGHT TO ALPHA
        else:
            return DEV_STATUS_PREALPHA_0_0_0  # staying at pre-alpha

    elif version.startswith("0.0."):
        if pending_major_bump:
            return DEV_STATUS_PROD_X_Y_Z  # MAJOR-BUMPPING STRAIGHT TO PROD
        elif pending_minor_bump:
            return DEV_STATUS_BETA_0_Y_Z  # MINOR-BUMPPING STRAIGHT TO BETA
        else:
            return DEV_STATUS_ALPHA_0_0_Z  # staying at alpha

    elif version.startswith("0."):
        if pending_major_bump:
            return DEV_STATUS_PROD_X_Y_Z  # MAJOR-BUMPPING STRAIGHT TO PROD
        else:
            return DEV_STATUS_BETA_0_Y_Z  # staying at beta

    elif int(version.split(".")[0]) >= 1:
        return DEV_STATUS_PROD_X_Y_Z

    else:
        raise Exception(f"Could not figure 'Development Status' for version: {version}")


class READMEMarkdownManager:
    """Add some automation to README.md."""

    def __init__(
        self,
        ffile: FromFiles,
        github_full_repo: str,
        gha_input: GHAInput,
        gh_api: GitHubAPI,
    ) -> None:
        self.ffile = ffile
        self.github_full_repo = github_full_repo
        self.bsec = gha_input
        self.gh_api = gh_api
        with open(ffile.readme_path) as f:
            lines_to_keep = []
            in_badges = False
            for line in f.readlines():
                if line.strip() == REAMDE_BADGES_START_DELIMITER:
                    in_badges = True
                    continue
                if line.strip() == REAMDE_BADGES_END_DELIMITER:
                    in_badges = False
                    continue
                if in_badges:
                    continue
                lines_to_keep.append(line)
        self.lines = self.badges_lines() + lines_to_keep

    @property
    def readme_path(self) -> Path:
        """Get the README file path."""
        return self.ffile.readme_path

    def badges_lines(self) -> list[str]:
        """Create and return the lines used to append to a README.md containing various linked-badges."""
        badges_line = ""

        # CircleCI badge
        if os.path.exists(f"{self.ffile.root}/.circleci/config.yml"):
            circleci = f"https://app.circleci.com/pipelines/github/{self.github_full_repo}?branch={self.gh_api.default_branch}&filter=all"
            badges_line += f"[![CircleCI](https://img.shields.io/circleci/build/github/{self.github_full_repo})]({circleci}) "

        # PyPI badge
        if self.bsec.pypi_name:
            badges_line += f"[![PyPI](https://img.shields.io/pypi/v/{self.bsec.pypi_name})](https://pypi.org/project/{self.bsec.pypi_name}/) "

        # GitHub Release badge
        badges_line += f"[![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/{self.github_full_repo}?include_prereleases)]({self.gh_api.url}/) "

        # Python versions
        if self.bsec.pypi_name:
            badges_line += f"[![Versions](https://img.shields.io/pypi/pyversions/{self.bsec.pypi_name}.svg)](https://pypi.org/project/{self.bsec.pypi_name}) "

        # PYPI License badge
        if self.bsec.pypi_name:
            badges_line += f"[![PyPI - License](https://img.shields.io/pypi/l/{self.bsec.pypi_name})]({self.gh_api.url}/blob/{self.gh_api.default_branch}/LICENSE) "

        # Other GitHub badges
        badges_line += (
            f"[![GitHub issues](https://img.shields.io/github/issues/{self.github_full_repo})]({self.gh_api.url}/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) "
            f"[![GitHub pull requests](https://img.shields.io/github/issues-pr/{self.github_full_repo})]({self.gh_api.url}/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen) "
        )

        return [
            REAMDE_BADGES_START_DELIMITER,
            "\n",
            badges_line.strip(),  # remove trailing whitespace
            "\n",
            REAMDE_BADGES_END_DELIMITER,
            "\n",  # only one newline here, otherwise we get an infinite commit-loop
        ]


TOMLDocumentIsh = Any  # TOMLDocument & mypy aren't friendly, so it's either this or a million 'ignore' comments


class PyProjectTomlBuilder:
    """Build out the `[project]`, `[semantic_release]`, and `[options]` sections in `toml_dict`.

    Create a 'READMEMarkdownManager' instance to write out, if needed.
    """

    def __init__(
        self,
        toml_dict: TOMLDocumentIsh,
        root_path: Path,
        github_full_repo: str,
        token: str,
        commit_message: str,
        gha_input: GHAInput,
    ):
        ffile = FromFiles(  # things requiring reading files
            root_path,
            gha_input,
            commit_message,
        )
        gh_api = GitHubAPI(github_full_repo, oauth_token=token)
        self._validate_repo_initial_state(toml_dict)

        # [build-system]
        toml_dict["build-system"] = {
            "requires": ["setuptools>=61.0"],
            "build-backend": "setuptools.build_meta",
        }

        # [project]
        # if we DON'T want PyPI stuff:
        if not gha_input.pypi_name:
            toml_dict["project"]["name"] = "_".join(ffile.packages).replace("_", "-")
            toml_dict["project"]["requires-python"] = gha_input.get_requires_python()
            # add the following if they were given:
            if gha_input.author or gha_input.author_email:
                toml_dict["project"]["authors"] = [{}]
                if gha_input.author:
                    toml_dict["project"]["authors"][0].update(
                        {"name": gha_input.author}
                    )
                if gha_input.author_email:
                    toml_dict["project"]["authors"][0].update(
                        {"email": gha_input.author_email}
                    )
            if gha_input.keywords:
                toml_dict["project"]["keywords"] = gha_input.keywords
        # if we DO want PyPI, then include everything:
        else:
            toml_dict["project"].update(
                {
                    "name": gha_input.pypi_name,
                    "authors": [
                        {
                            "name": gha_input.author,
                            "email": gha_input.author_email,
                        }
                    ],
                    "description": gh_api.description,
                    "readme": ffile.readme_path.name,
                    "license": {"file": "LICENSE"},
                    "keywords": gha_input.keywords,
                    "classifiers": (
                        [
                            get_development_status(
                                toml_dict["project"]["version"],
                                gha_input.patch_without_tag,
                                commit_message,
                            )
                        ]
                        + gha_input.python_classifiers()
                    ),
                    "requires-python": gha_input.get_requires_python(),
                }
            )
            # [project.urls]
            toml_dict["project"]["urls"] = {
                "Homepage": f"https://pypi.org/project/{gha_input.pypi_name}/",
                "Tracker": f"{gh_api.url}/issues",
                "Source": gh_api.url,
            }

        # [tool]
        if not toml_dict.get("tool"):
            toml_dict["tool"] = {}

        # [tool.semantic_release] -- will be completely overridden
        toml_dict["tool"]["semantic_release"] = {
            "version_toml": ["pyproject.toml:project.version"],
            # "wipac_dev_tools/__init__.py:__version__"
            # "wipac_dev_tools/__init__.py:__version__,wipac_foo_tools/__init__.py:__version__"
            "version_variables": [
                f"{p}:__version__"
                for p in ffile.get_dunder_version_inits(toml_dict["project"]["version"])
            ],
            # the emoji parser is the simplest parser and does not require angular-style commits
            "commit_parser": "emoji",
            "commit_parser_options": {
                "major_tags": SEMANTIC_RELEASE_MAJOR,
                "minor_tags": SEMANTIC_RELEASE_MINOR,
                "patch_tags": (
                    SEMANTIC_RELEASE_PATCH
                    if not gha_input.patch_without_tag
                    else SEMANTIC_RELEASE_PATCH + sorted(PATCH_WITHOUT_TAG_WORKAROUND)
                ),
            },
            # this is required fo the package to be pushed to pypi (by the pypa GHA)
            "build_command": "pip install build && python -m build",
        }

        # [tool.setuptools]
        if not toml_dict["tool"].get("setuptools"):
            toml_dict["tool"]["setuptools"] = {}
        toml_dict["tool"]["setuptools"].update(
            {
                "packages": {
                    "find": self._tool_setuptools_packages_find(gha_input),
                },
                "package-data": {
                    **toml_dict["tool"].get("setuptools", {}).get("package-data", {}),
                    "*": self._tool_setuptools_packagedata_star(toml_dict),
                },
            }
        )

        # [project.optional-dependencies][mypy]
        if gha_input.auto_mypy_option:
            try:
                toml_dict["project"]["optional-dependencies"]["mypy"] = sorted(
                    set(
                        itertools.chain.from_iterable(
                            deps
                            for opt, deps in toml_dict["project"][
                                "optional-dependencies"
                            ].items()
                            if opt != "mypy"
                        )
                    )
                )
            except KeyError:
                pass  # there are no [project.optional-dependencies]

        # Automate some README stuff
        self.readme_mgr: READMEMarkdownManager | None
        if ffile.readme_path.suffix == ".md":
            self.readme_mgr = READMEMarkdownManager(
                ffile, github_full_repo, gha_input, gh_api
            )
        else:
            self.readme_mgr = None

    @staticmethod
    def _validate_repo_initial_state(toml_dict: TOMLDocumentIsh) -> None:
        # must have these fields...
        try:
            toml_dict["project"]["version"]
        except KeyError:
            raise Exception("pyproject.toml must have 'project.version'")

    @staticmethod
    def _tool_setuptools_packages_find(gha_input: GHAInput) -> dict[str, Any]:
        # only allow these...
        if gha_input.package_dirs:
            return {
                "include": gha_input.package_dirs
                + [f"{p}.*" for p in gha_input.package_dirs]
            }
        # disallow these...
        dicto: dict[str, Any] = {"namespaces": False}
        if gha_input.exclude_dirs:
            dicto.update({"exclude": gha_input.exclude_dirs})
        return dicto

    @staticmethod
    def _tool_setuptools_packagedata_star(toml_dict: TOMLDocumentIsh) -> list[str]:
        """Add py.typed to "*"."""
        try:
            current = set(toml_dict["tool"]["setuptools"]["package-data"]["*"])
        except KeyError:
            return ["py.typed"]

        if "py.typed" in current:
            return list(current)
        else:
            return list(current) + ["py.typed"]


def set_multiline_array(
    toml_dict: TOMLDocument,
    *path: str,
    sort: bool = False,
) -> None:
    """Convert the list at the given dotted path into a multiline TOML array."""
    cur = toml_dict
    for key in path[:-1]:
        cur = cur.get(key)  # type: ignore[assignment]
        if cur is None:
            return  # path doesn't exist
    last_key = path[-1]
    val = cur.get(last_key)
    if isinstance(val, list):
        if sort:
            cur[last_key] = array(sorted(val)).multiline(True)  # type: ignore[arg-type]
        else:
            cur[last_key] = array(val).multiline(True)  # type: ignore[arg-type]


def write_toml(
    toml_file: Path,
    github_full_repo: str,
    token: str,
    commit_message: str,
    gha_input: GHAInput,
) -> READMEMarkdownManager | None:
    """Build/write the `pyproject.toml` sections according to `BUILDER_SECTION_NAME`.

    Return a 'READMEMarkdownManager' instance to write out. If, necessary.
    """
    toml_file = toml_file.resolve()
    if toml_file.exists():
        with open(toml_file, "r") as f:
            toml_dict = tomlkit.load(f)
    else:
        toml_dict = TOMLDocument()

    builder = PyProjectTomlBuilder(
        toml_dict,  # updates this
        toml_file.parent,
        github_full_repo,
        token,
        commit_message,
        gha_input,
    )

    # Make specific arrays multiline
    set_multiline_array(toml_dict, "project", "dependencies", sort=True)
    set_multiline_array(toml_dict, "project", "keywords")
    set_multiline_array(toml_dict, "project", "classifiers")
    optional_deps = toml_dict.get("project", {}).get("optional-dependencies", {})
    for key in optional_deps:
        set_multiline_array(optional_deps, key, sort=True)

    with open(toml_file, "w") as f:
        tomlkit.dump(toml_dict, f)

    return builder.readme_mgr


def work(
    toml_file: Path,
    github_full_repo: str,
    token: str,
    commit_message: str,
    gha_input: GHAInput,
) -> None:
    """Build & write the pyproject.toml. Write the readme if necessary."""
    readme_mgr = write_toml(
        toml_file,
        github_full_repo,
        token,
        commit_message,
        gha_input,
    )

    if readme_mgr:
        with open(readme_mgr.readme_path, "w") as f:
            for line in readme_mgr.lines:
                f.write(line)


def main() -> None:
    """Read and write all necessary files."""
    parser = argparse.ArgumentParser(
        description=f"Read/transform 'pyproject.toml' and 'README.md' files. "
        f"Builds out 'pyproject.toml' sections according to [{BUILDER_SECTION_NAME}].",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--toml",
        type=lambda x: argparse_tools.validate_arg(
            Path(x),
            Path(x).name == "pyproject.toml",
            ValueError("toml file needs to be named 'pyproject.toml'"),
        ),
        required=True,
        help="path to the 'pyproject.toml' file",
    )
    parser.add_argument(
        "--github-full-repo",
        type=lambda x: argparse_tools.validate_arg(
            x,
            bool(re.match(r"(\w|-)+/(\w|-)+$", x)),
            ValueError("Not a valid GitHub repo"),
        ),
        required=True,
        help="Fully-named GitHub repo, ex: WIPACrepo/wipac-dev-tools",
    )
    parser.add_argument(
        "--token",
        required=True,
        help="An OAuth2 token, usually GITHUB_TOKEN",
    )

    def coerce_python_version(val: str | None) -> None | tuple[int, int]:
        if not val:
            return None
        # will raise error if not good format
        return tuple(int(d) for d in val.split(".", maxsplit=1))  # type: ignore[return-value]

    # From Client GitHub Action Input
    # REQUIRED
    parser.add_argument(
        "--python-min",
        # "3.12" -> (3,12)
        type=coerce_python_version,
        required=True,
        help="Minimum required Python version",
    )
    # OPTIONAL (python)
    parser.add_argument(
        "--python-max",
        # "3.12" -> (3,12)
        type=coerce_python_version,
        default=None,
        help="Maximum supported Python version. If not provided, the most recent Python version will be used.",
    )
    # OPTIONAL (packaging)
    parser.add_argument(
        "--package-dirs",
        nargs="*",
        type=str,
        default=[],
        help="List of directories to release. If not provided, all packages in the repository's root directory will be used.",
    )
    parser.add_argument(
        "--exclude-dirs",
        nargs="*",
        type=str,
        default=[],
        help="List of directories to exclude from release, relative to the repository's root directory.",
    )
    # OPTIONAL (releases)
    parser.add_argument(
        "--pypi-name",
        type=str,
        default="",
        help="Name of the PyPI package",
    )
    parser.add_argument(
        "--patch-without-tag",
        type=strtobool,
        default=True,
        help="Whether to make a patch release even if the commit message does not explicitly warrant one",
    )
    # OPTIONAL (meta)
    parser.add_argument(
        "--keywords",
        type=lambda x: [k.strip() for k in x.split(",")],
        default=[],
        help="keywords",
    )
    parser.add_argument(
        "--author",
        type=str,
        default="",
        help="Author of the package (required if the package is intended to be hosted on PyPI)",
    )
    parser.add_argument(
        "--author-email",
        type=str,
        default="",
        help="Email of the package author (required if the package is intended to be hosted on PyPI)",
    )
    parser.add_argument(
        "--license",
        type=str,
        default="",
        help="Repository's license type",
    )
    parser.add_argument(
        "--auto-mypy-option",
        type=strtobool,
        default=False,
        help="Whether to auto create/update the 'mypy' install option plus its dependencies",
    )
    args = parser.parse_args()
    logging_tools.set_level("DEBUG", LOGGER, use_coloredlogs=True)
    logging_tools.log_argparse_args(args, logger=LOGGER)

    gha_input = GHAInput(
        **{
            k: v
            for k, v in vars(args).items()
            # use arg if it has non-falsy value -- otherwise, rely on default
            if v and (k in [f.name for f in dataclasses.fields(GHAInput)])
        },
    )
    LOGGER.info(gha_input)

    commit_message = (  # retrieving this in bash is messy since the string can include any character
        subprocess.check_output("git log -1 --pretty=%B".split())
        .decode("utf-8")
        .strip()
    )
    LOGGER.info(f"{commit_message=}")

    work(
        args.toml,
        args.github_full_repo,
        args.token,
        commit_message,
        gha_input,
    )


if __name__ == "__main__":
    main()
