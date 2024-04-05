"""Module to build `pyproject.toml` sections for use by `setup.py`/`setuptools`.

Used in CI/CD, used by GH Action.
"""

import argparse
import dataclasses
import logging
import os
import re
from pathlib import Path
from typing import Iterator, cast

import dacite
import requests
import toml
from wipac_dev_tools import (
    argparse_tools,
    logging_tools,
    semver_parser_tools,
)

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
    if chr(i) not in ['"', ","]  # else upsets toml syntax
]

DEV_STATUS_PREALPHA_0_0_0 = "Development Status :: 2 - Pre-Alpha"
DEV_STATUS_ALPHA_0_0_Z = "Development Status :: 3 - Alpha"
DEV_STATUS_BETA_0_Y_Z = "Development Status :: 4 - Beta"
DEV_STATUS_PROD_X_Y_Z = "Development Status :: 5 - Production/Stable"

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
    license: str = "MIT"

    def __post_init__(self) -> None:
        if self.pypi_name:
            if not self.keywords or not self.author or not self.author_email:
                raise Exception(
                    "'keywords', 'author', and 'author_email' must be provided when "
                    "'pypi_name' is `True`"
                )
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

    def python_requires(self) -> str:
        """Get a `[project]/python_requires` string from `self.python_range`.

        Ex: "">=3.6, <3.10" (cannot do "<=3.9" because 3.9.1 > 3.9)
        """
        return f">={self.python_min[0]}.{self.python_min[1]}, <{self.python_max[0]}.{self.python_max[1]+1}"

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
        dirs_exclude: list[str],
        commit_message: str,
    ) -> None:
        if not os.path.exists(root):
            raise NotADirectoryError(root)
        self.gha_input = gha_input
        self.root = root.resolve()

        pkg_paths = self._get_package_paths(dirs_exclude)
        self.packages = [p.name for p in pkg_paths]
        self.version = self._get_version(pkg_paths)

        self.readme_path = self._get_readme_path()
        self.development_status = self._get_development_status(commit_message)

    def _get_package_paths(self, dirs_exclude: list[str]) -> list[Path]:
        """Find the package path(s)."""

        def _get_packages() -> Iterator[str]:
            """This is essentially [options]'s `packages = find:`."""
            for directory in [p for p in self.root.iterdir() if p.is_dir()]:
                if directory.name in dirs_exclude:
                    continue
                if "__init__.py" in [p.name for p in directory.iterdir()]:
                    yield directory.name

        if not (available_pkgs := list(_get_packages())):
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

    @staticmethod
    def _get_version(pkg_paths: list[Path]) -> str:
        """Get the package's `__version__` string.

        This is essentially [project]'s `version = attr: <module-path to __version__>`.

        `__version__` needs to be parsed as plain text due to potential
        race condition, see:
        https://stackoverflow.com/a/2073599/13156561
        """

        def version(ppath: Path) -> str:
            with open(ppath / "__init__.py") as f:
                for line in f.readlines():
                    if "__version__" in line:
                        # grab "X.Y.Z" from `__version__ = 'X.Y.Z'`
                        # - quote-style insensitive
                        return line.replace('"', "'").split("=")[-1].split("'")[1]

            raise Exception(f"Cannot find __version__ in {ppath}/__init__.py")

        pkg_versions = {p: version(p) for p in pkg_paths}
        if len(set(pkg_versions.values())) != 1:
            raise Exception(
                f"Version mismatch between packages: {pkg_versions}. "
                f"All __version__ tuples must be the same."
            )
        return list(pkg_versions.values())[0]

    def _get_development_status(self, commit_message: str) -> str:
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
        pending_patch_bump = self.gha_input.patch_without_tag or any(
            k in commit_message for k in SEMANTIC_RELEASE_PATCH
        )

        # NOTE - if someday we abandon python-semantic-release, this is a starting place to detect the next version -- in this case, we'd change the version number before merging to main

        if self.version == "0.0.0":
            if pending_major_bump:
                return DEV_STATUS_PROD_X_Y_Z  # MAJOR-BUMPPING STRAIGHT TO PROD
            elif pending_minor_bump:
                return DEV_STATUS_BETA_0_Y_Z  # MINOR-BUMPPING STRAIGHT TO BETA
            elif pending_patch_bump:
                return DEV_STATUS_ALPHA_0_0_Z  # PATCH-BUMPPING STRAIGHT TO ALPHA
            else:
                return DEV_STATUS_PREALPHA_0_0_0  # staying at pre-alpha

        elif self.version.startswith("0.0."):
            if pending_major_bump:
                return DEV_STATUS_PROD_X_Y_Z  # MAJOR-BUMPPING STRAIGHT TO PROD
            elif pending_minor_bump:
                return DEV_STATUS_BETA_0_Y_Z  # MINOR-BUMPPING STRAIGHT TO BETA
            else:
                return DEV_STATUS_ALPHA_0_0_Z  # staying at alpha

        elif self.version.startswith("0."):
            if pending_major_bump:
                return DEV_STATUS_PROD_X_Y_Z  # MAJOR-BUMPPING STRAIGHT TO PROD
            else:
                return DEV_STATUS_BETA_0_Y_Z  # staying at beta

        elif int(self.version.split(".")[0]) >= 1:
            return DEV_STATUS_PROD_X_Y_Z

        else:
            raise Exception(
                f"Could not figure 'Development Status' for version: {self.version}"
            )


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
        badges = [REAMDE_BADGES_START_DELIMITER, "\n"]

        # CircleCI badge
        circleci = f"https://app.circleci.com/pipelines/github/{self.github_full_repo}?branch={self.gh_api.default_branch}&filter=all"
        if os.path.exists(f"{self.ffile.root}/.circleci/config.yml"):
            badges.append(
                f"[![CircleCI](https://img.shields.io/circleci/build/github/{self.github_full_repo})]({circleci}) "
            )

        # PyPI badge
        if self.bsec.pypi_name:
            badges.append(
                f"[![PyPI](https://img.shields.io/pypi/v/{self.bsec.pypi_name})](https://pypi.org/project/{self.bsec.pypi_name}/) "
            )

        # GitHub Release badge
        badges.append(
            f"[![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/{self.github_full_repo}?include_prereleases)]({self.gh_api.url}/) ",
        )

        # PYPI License badge
        if self.bsec.pypi_name:
            badges.append(
                f"[![PyPI - License](https://img.shields.io/pypi/l/{self.bsec.pypi_name})]({self.gh_api.url}/blob/{self.gh_api.default_branch}/LICENSE) "
            )

        # Other GitHub badges
        badges += [
            f"[![Lines of code](https://img.shields.io/tokei/lines/github/{self.github_full_repo})]({self.gh_api.url}/) ",
            f"[![GitHub issues](https://img.shields.io/github/issues/{self.github_full_repo})]({self.gh_api.url}/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) ",
            f"[![GitHub pull requests](https://img.shields.io/github/issues-pr/{self.github_full_repo})]({self.gh_api.url}/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen) ",
        ]

        # Ending Stuff
        badges += [
            "\n",
            REAMDE_BADGES_END_DELIMITER,
            "\n",  # only one newline here, otherwise we get an infinite commit-loop
        ]

        return badges


def _build_out_sections(
    toml_dict: dict,
    root_path: Path,
    github_full_repo: str,
    token: str,
    commit_message: str,
    gha_input: GHAInput,
) -> READMEMarkdownManager | None:
    """Build out the `[project]`, `[semantic_release]`, and `[options]` sections in `toml_dict`.

    Return a 'READMEMarkdownManager' instance to write out. If, necessary.
    """
    ffile = FromFiles(  # things requiring reading files
        root_path,
        gha_input,
        gha_input.exclude_dirs,
        commit_message,
    )
    gh_api = GitHubAPI(github_full_repo, oauth_token=token)

    # [build-system]
    toml_dict["build-system"] = {
        "requires": ["setuptools>=61.0"],
        "build-backend": "setuptools.build_meta",
    }

    # [project]
    if not toml_dict.get("project"):
        toml_dict["project"] = {}
    # always add these fields
    toml_dict["project"].update(
        {
            "find": {"namespaces": False},
            "version": toml_dict.get("project", {}).get("version", "0.0.0"),
        }
    )
    # if we DON'T want PyPI stuff:
    if not gha_input.pypi_name:
        toml_dict["project"]["name"] = "_".join(ffile.packages).replace("_", "-")
        # add the following if they were given:
        if gha_input.author:
            toml_dict["project"]["author"] = gha_input.author
        if gha_input.author_email:
            toml_dict["project"]["author_email"] = gha_input.author_email
        if gha_input.keywords:
            toml_dict["project"]["keywords"] = gha_input.keywords
    # if we DO want PyPI, then include everything:
    else:
        toml_dict["project"].update(
            {
                "name": gha_input.pypi_name,
                "url": gh_api.url,
                "author": gha_input.author,
                "author_email": gha_input.author_email,
                "description": gh_api.description,
                "readme": ffile.readme_path.name,
                "license": gha_input.license,
                "keywords": gha_input.keywords,
                "classifiers": [
                    ffile.development_status,
                    "License :: OSI Approved :: MIT License",
                ]
                + gha_input.python_classifiers(),
                "requires-python": gha_input.python_requires(),
            }
        )
        # [project.urls]
        toml_dict["project.urls"] = dict(
            Homepage=f"https://pypi.org/project/{gha_input.pypi_name}/",
            Tracker=f"{gh_api.url}/issues",
            Source=gh_api.url,
        )

    # [tool.semantic_release] -- will be completely overridden
    toml_dict["tool.semantic_release"] = dict(
        version_toml=["pyproject.toml:project.version"],
        commit_parser="emoji",
        commit_parser_options=dict(
            major_tags=SEMANTIC_RELEASE_MAJOR,
            minor_tags=SEMANTIC_RELEASE_MINOR,
            patch_tags=(
                SEMANTIC_RELEASE_PATCH
                if not gha_input.patch_without_tag
                else SEMANTIC_RELEASE_PATCH + sorted(PATCH_WITHOUT_TAG_WORKAROUND)
            ),
        ),
    )

    # [tool.setuptools.packages.find]
    toml_dict["tool.setuptools.packages.find"] = {}
    if gha_input.package_dirs:
        toml_dict["tool.setuptools.packages.find"]["include"] = (
            gha_input.package_dirs + [f"{p}.*" for p in gha_input.package_dirs]
        )
    if gha_input.exclude_dirs:
        toml_dict["tool.setuptools.packages.find"]["exclude"] = gha_input.exclude_dirs

    # [tool.setuptools.package-data]
    if not toml_dict.get("tool.setuptools.package-data"):
        # will only override some fields
        toml_dict["tool.setuptools.package-data"] = {}
    if "py.typed" not in toml_dict["tool.setuptools.package-data"].get("*", ""):
        if not toml_dict["tool.setuptools.package-data"].get("*"):
            toml_dict["tool.setuptools.package-data"]["*"] = ["py.typed"]
        else:  # append to existing list
            toml_dict["tool.setuptools.package-data"]["*"].append("py.typed")

    # Automate some README stuff
    if ffile.readme_path.suffix == ".md":
        return READMEMarkdownManager(ffile, github_full_repo, gha_input, gh_api)
    return None


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
            toml_dict = toml.load(f)
    else:
        toml_dict = {}

    readme_mgr = _build_out_sections(
        toml_dict,
        toml_file.parent,
        github_full_repo,
        token,
        commit_message,
        gha_input,
    )

    with open(toml_file, "w") as f:
        toml.dump(toml_dict, f)

    return readme_mgr


def main(
    toml_file: Path,
    github_full_repo: str,
    token: str,
    commit_message: str,
    gha_input: GHAInput,
) -> None:
    """Read and write all necessary files."""
    # build & write the pyproject.toml
    readme_mgr = write_toml(
        toml_file,
        github_full_repo,
        token,
        commit_message,
        gha_input,
    )

    # also, write the readme, if necessary
    if readme_mgr:
        with open(readme_mgr.readme_path, "w") as f:
            for line in readme_mgr.lines:
                f.write(line)


if __name__ == "__main__":
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
    parser.add_argument(
        "--commit-message",
        required=True,
        help="the current commit message -- used for extracting versioning info",
    )

    # From Client GitHub Action Input
    # REQUIRED
    parser.add_argument(
        "--python-min",
        type=str,
        required=True,
        help="Minimum required Python version",
    )
    # OPTIONAL (python)
    parser.add_argument(
        "--python-max",
        type=str,
        default="",
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
        type=bool,
        default=True,
        help="Whether to make a patch release even if the commit message does not explicitly warrant one",
    )
    # OPTIONAL (meta)
    parser.add_argument(
        "--keywords",
        nargs="*",
        type=str,
        default=[],
        help="Space-separated list of keywords",
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

    args = parser.parse_args()
    logging_tools.log_argparse_args(args, logger=LOGGER, level="WARNING")
    print(args)
    main(
        args.toml,
        args.github_full_repo,
        args.token,
        args.commit_message,
        dacite.from_dict(
            GHAInput,
            {
                k: v
                for k, v in vars(args).items()
                # use arg if it has non-falsy value -- otherwise, use default
                if k in dataclasses.fields(GHAInput) and v
            },
        ),
    )
