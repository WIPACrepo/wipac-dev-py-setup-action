"""Module to build `setup.cfg` sections for use by `setup.py`/`setuptools`.

Used in CI/CD, used by GH Action.
"""

# docfmt: skip-file-ric-evans

import argparse
import configparser
import dataclasses
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, cast

import requests
from wipac_dev_tools import argparse_tools, logging_tools

BUILDER_SECTION_NAME = "wipac:cicd_setup_builder"
GENERATED_STR = f"generated by {BUILDER_SECTION_NAME}"
REAMDE_BADGES_START_DELIMITER = "<!--- Top of README Badges (automated) --->"
REAMDE_BADGES_END_DELIMITER = "<!--- End of README Badges (automated) --->"

_PYTHON_MINOR_RELEASE_MAX = 50

LOGGER = logging.getLogger("setup-builder")

PythonMinMax = Tuple[Tuple[int, int], Tuple[int, int]]


def get_latest_py3_release() -> Tuple[int, int]:
    """Return the latest python3 release version as tuple."""
    minor = 10  # start with 3.10
    while True:
        url = f"https://docs.python.org/release/3.{minor}.0/"
        if requests.get(url).status_code >= 300:  # not a success (404 likely)
            return (3, minor - 1)
        if minor == _PYTHON_MINOR_RELEASE_MAX:
            raise Exception(
                "Latest python-release detection failed (unless python 3.50 is real?)"
            )
        minor += 1


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
class Section:
    """Encapsulate a setup.cfg section."""

    def add_unique_fields(self, dict_in: Dict[str, Any]) -> Dict[str, Any]:
        """Merge `dict_in` to a dict-cast copy of `self`.

        `self` is given precedence for duplicate keys.
        """
        return {**dict_in, **dataclasses.asdict(self)}


@dataclasses.dataclass
class BuilderSection(Section):
    """Encapsulates the `BUILDER_SECTION_NAME` section & checks for required/invalid fields."""

    python_min: str  # python_requires
    author: str = ""
    author_email: str = ""
    pypi_name: str = ""  # enables PyPI publishing, badges, sections, etc.
    python_max: str = ""  # python_requires
    package_dirs: str = ""
    keywords_spaced: str = ""  # comes as "A B C"

    def __post_init__(self) -> None:
        if self.pypi_name:
            if not self.author or not self.author_email:
                raise Exception(
                    "'author' and 'author_email' must be provided in "
                    "setup.cfg ([wipac:cicd_setup_builder]) when "
                    "'pypi_name' is given (PyPI-metadata mode)"
                )

    def _python3_min_max(self) -> PythonMinMax:
        """Get the `PythonMinMax` version of `self.python_min`."""

        def get_py3_minor(py_release: str, attr_name: str) -> int:
            m = re.match(r"(?P<maj>\d+)\.(?P<min>\d+)$", py_release)
            if not m:
                raise Exception(f"'{attr_name}' is not a valid release: '{py_release}'")

            major, minor = int(m.groupdict()["maj"]), int(m.groupdict()["min"])

            if major < 3:
                raise Exception(
                    f"Python-release automation ('{attr_name}') does not work for python <3."
                )
            if major >= 4:
                raise Exception(
                    f"Python-release automation ('{attr_name}') does not work for python 4+."
                )

            return minor

        min_minor = get_py3_minor(self.python_min, "python_min")
        if not self.python_max:
            versions = ((3, min_minor), get_latest_py3_release())
        else:
            max_minor = get_py3_minor(self.python_max, "python_max")
            versions = ((3, min_minor), (3, max_minor))

        return cast(PythonMinMax, tuple(sorted(versions)))

    def python_requires(self) -> str:
        """Get a `[metadata]/python_requires` string from `self.python_range`.

        Ex: "">=3.6, <3.10" (cannot do "<=3.9" because 3.9.1 > 3.9)
        """
        py_min_max = self._python3_min_max()
        return f">={py_min_max[0][0]}.{py_min_max[0][1]}, <{py_min_max[1][0]}.{py_min_max[1][1]+1}"

    def python_classifiers(self) -> List[str]:
        """Get auto-detected `Programming Language :: Python :: *` list.

        NOTE: Will not work after the '3.* -> 4.0'-transition.
        """
        py_min_max = self._python3_min_max()

        return [
            f"Programming Language :: Python :: 3.{r}"
            for r in range(py_min_max[0][1], py_min_max[1][1] + 1)
        ]

    def packages(self) -> List[str]:
        """Get a list of directories for Python packages."""
        return self.package_dirs.strip().split()

    def keywords_list(self, base_keywords: List[str]) -> List[str]:
        """Get the user-defined keywords as a list, along with any base keywords."""
        keywords = []
        phrase = []
        for word in self.keywords_spaced.strip().split():
            # "foo" -> strip & add
            if word.startswith('"') and word.endswith('"'):
                keywords.append(word.strip('"'))
            # "BAR -> store
            elif word.startswith('"'):
                phrase = [word.lstrip('"')]
            # BAZ" -> pop & add phrase
            elif word.endswith('"'):
                phrase.append(word.rstrip('"'))
                keywords.append(" ".join(phrase))
                phrase = []
            # are we within quotes? prev: "BAR; now: bat; later: BAZ" ("BAR bat BAZ")
            elif phrase:
                phrase.append(word)
            # normal case (not within quotes)
            else:
                keywords.append(word)

        keywords.extend(base_keywords)

        if not keywords and self.pypi_name:
            raise Exception(
                "keywords must be provided in setup.cfg ([wipac:cicd_setup_builder]) "
                "when 'pypi_name' is given (PyPI-metadata mode)"
            )
        return keywords


@dataclasses.dataclass
class MetadataSection(Section):
    """Encapsulates the *minimal* `[metadata]` section & checks for required/invalid fields."""

    name: str
    version: str
    url: str
    author: str
    author_email: str
    description: str
    long_description: str
    long_description_content_type: str
    keywords: str
    license: str
    classifiers: str
    download_url: str
    project_urls: str


@dataclasses.dataclass
class OptionsSection(Section):
    """Encapsulates the *minimal* `[options]` section & checks for required/invalid fields."""

    python_requires: str
    install_requires: str
    packages: str

    def __post_init__(self) -> None:
        # sort requirements if they're dangling
        if "\n" in self.install_requires.strip():
            as_lines = self.install_requires.strip().split("\n")
            self.install_requires = list_to_dangling(as_lines, sort=True)


def list_to_dangling(lines: List[str], sort: bool = False) -> str:
    """Create a "dangling" multi-line formatted list."""
    stripped = [ln.strip() for ln in lines]  # strip each
    stripped = [ln for ln in stripped if ln]  # kick each out if its empty
    return "\n" + "\n".join(sorted(stripped) if sort else stripped)


def long_description_content_type(readme_path: Path) -> str:
    """Return the long_description_content_type for the given file extension."""
    match readme_path.suffix:
        case ".md":
            return "text/markdown"
        case ".rst":
            return "text/x-rst"
        case _:
            return "text/plain"


class FromFiles:
    """Get things that require reading files."""

    def __init__(
        self, root: Path, bsec: BuilderSection, dirs_exclude: List[str]
    ) -> None:
        if not os.path.exists(root):
            raise NotADirectoryError(root)
        self._bsec = bsec
        self.root = root.resolve()

        pkg_paths = self._get_package_paths(dirs_exclude)
        self.packages = [p.name for p in pkg_paths]
        self.version = self._get_version(pkg_paths)

        self.readme_path = self._get_readme_path()
        self.development_status = self._get_development_status()

    def _get_package_paths(self, dirs_exclude: List[str]) -> List[Path]:
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

        # check the setup.cfg: package_dirs
        if self._bsec.packages():
            if not_ins := [p for p in self._bsec.packages() if p not in available_pkgs]:
                if len(not_ins) == 1:
                    raise Exception(
                        f"Package directory not found: "
                        f"{not_ins[0]} (defined in setup.cfg). "
                        f"Is the directory missing an __init__.py?"
                    )
                raise Exception(
                    f"Package directories not found: "
                    f"{', '.join(not_ins)} (defined in setup.cfg). "
                    f"Are the directories missing __init__.py files?"
                )

            return [self.root / p for p in self._bsec.packages()]
        # use the auto-detected package (if there's ONE)
        else:
            if len(available_pkgs) > 1:
                raise Exception(
                    f"More than one package found in '{self.root}': {', '.join(available_pkgs)}. "
                    f"Either "
                    f"[1] list *all* your desired packages in your setup.cfg's 'package_dirs', "
                    f"[2] remove the extra __init__.py file(s), "
                    f"or [3] list which packages to ignore in your GitHub Action step's 'with.directory-exclude'."
                )
            return [self.root / available_pkgs[0]]

    def _get_readme_path(self) -> Path:
        """Return the 'README' file and its extension."""
        for fname in self.root.iterdir():
            if fname.stem == "README":
                return Path(fname)
        raise FileNotFoundError(f"No README file found in '{self.root}'")

    @staticmethod
    def _get_version(pkg_paths: List[Path]) -> str:
        """Get the package's `__version__` string.

        This is essentially [metadata]'s `version = attr: <module-path to __version__>`.

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

    def _get_development_status(self) -> str:
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
        if self.version.startswith("0.0.0"):
            return "Development Status :: 2 - Pre-Alpha"
        elif self.version.startswith("0.0."):
            return "Development Status :: 3 - Alpha"
        elif self.version.startswith("0."):
            return "Development Status :: 4 - Beta"
        elif int(self.version.split(".")[0]) >= 1:
            return "Development Status :: 5 - Production/Stable"
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
        bsec: BuilderSection,
        gh_api: GitHubAPI,
    ) -> None:
        self.ffile = ffile
        self.github_full_repo = github_full_repo
        self.bsec = bsec
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

    def badges_lines(self) -> List[str]:
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
    cfg: configparser.RawConfigParser,
    root_path: Path,
    github_full_repo: str,
    base_keywords: List[str],
    dirs_exclude: List[str],
    repo_license: str,
    token: str,
) -> Optional[READMEMarkdownManager]:
    """Build out the `[metadata]`, `[semantic_release]`, and `[options]` sections in `cfg`.

    Return a 'READMEMarkdownManager' instance to write out. If, necessary.
    """
    bsec = BuilderSection(**dict(cfg[BUILDER_SECTION_NAME]))  # checks req/extra fields
    ffile = FromFiles(root_path, bsec, dirs_exclude)  # things requiring reading files
    gh_api = GitHubAPI(github_full_repo, oauth_token=token)

    # [metadata]
    if not cfg.has_section("metadata"):  # will only override some fields
        cfg["metadata"] = {}
    meta_version_single = (  # even if there are >1 packages, use just one (they're all the same)
        f"attr: {ffile.packages[0]}.__version__"  # "wipac_dev_tools.__version__"
    )
    # if we DON'T want PyPI stuff:
    if not bsec.pypi_name:
        cfg["metadata"]["version"] = meta_version_single
        if bsec.author:
            cfg["metadata"]["author"] = bsec.author
        if bsec.author_email:
            cfg["metadata"]["author_email"] = bsec.author_email
        if bsec.keywords_list(base_keywords):
            cfg["metadata"]["keywords"] = list_to_dangling(
                bsec.keywords_list(base_keywords)
            )
    # if we DO want PyPI, then include everything:
    else:
        msec = MetadataSection(
            name=bsec.pypi_name,
            version=meta_version_single,
            url=gh_api.url,
            author=bsec.author,
            author_email=bsec.author_email,
            description=gh_api.description,
            long_description=f"file: {ffile.readme_path.name}",
            long_description_content_type=long_description_content_type(
                ffile.readme_path
            ),
            keywords=list_to_dangling(bsec.keywords_list(base_keywords)),
            license=repo_license,
            classifiers=list_to_dangling(
                [ffile.development_status]
                + ["License :: OSI Approved :: MIT License"]
                + bsec.python_classifiers(),
            ),
            download_url=f"https://pypi.org/project/{bsec.pypi_name}/",
            project_urls=list_to_dangling(
                [
                    f"Tracker = {gh_api.url}/issues",
                    f"Source = {gh_api.url}",
                    # f"Documentation = {}",
                ],
            ),
        )
        cfg["metadata"] = msec.add_unique_fields(dict(cfg["metadata"]))

    # [semantic_release]
    cfg.remove_section("semantic_release")  # will be completely overridden
    cfg["semantic_release"] = {
        # "wipac_dev_tools/__init__.py:__version__"
        # "wipac_dev_tools/__init__.py:__version__,wipac_foo_tools/__init__.py:__version__"
        "version_variable": ",".join(
            f"{p}/__init__.py:__version__" for p in ffile.packages
        ),
        "upload_to_pypi": "True" if bsec.pypi_name else "False",  # >>> str(bool(x))
        "patch_without_tag": "True",
        "commit_parser": "semantic_release.history.emoji_parser",
        "major_emoji": "[major]",
        "minor_emoji": "[minor]",
        "patch_emoji": "[fix], [patch]",
        "branch": gh_api.default_branch,
    }

    # [options]
    if not cfg.has_section("options"):  # will only override some fields
        cfg["options"] = {}
    osec = OptionsSection(
        python_requires=bsec.python_requires(),
        packages="find:",  # always use "find:", then use include/exclude
        install_requires=cfg["options"].get("install_requires", fallback=""),
    )
    cfg["options"] = osec.add_unique_fields(dict(cfg["options"]))

    # [options.packages.find]
    if cfg["options"]["packages"] == "find:":
        cfg["options.packages.find"] = {}
        if bsec.packages():
            cfg["options.packages.find"]["include"] = list_to_dangling(
                bsec.packages() + [f"{p}.*" for p in bsec.packages()]
            )
        if dirs_exclude:
            cfg["options.packages.find"]["exclude"] = list_to_dangling(dirs_exclude)

    # [options.package_data]
    if not cfg.has_section("options.package_data"):  # will only override some fields
        cfg["options.package_data"] = {}
    if "py.typed" not in cfg["options.package_data"].get("*", fallback=""):
        if not cfg["options.package_data"].get("*"):
            star_data = "py.typed"
        else:  # append to existing list
            star_data = f"py.typed, {cfg['options.package_data']['*']}"
        cfg["options.package_data"]["*"] = star_data

    # Automate some README stuff
    if ffile.readme_path.suffix == ".md":
        return READMEMarkdownManager(ffile, github_full_repo, bsec, gh_api)
    return None


class MissingSectionException(Exception):
    """Raise when the wanted section is missing."""


def write_setup_cfg(
    setup_cfg: Path,
    github_full_repo: str,
    base_keywords: List[str],
    dirs_exclude: List[str],
    repo_license: str,
    token: str,
    commit_message: str,
) -> Optional[READMEMarkdownManager]:
    """Build/write the `setup.cfg` sections according to `BUILDER_SECTION_NAME`.

    Return a 'READMEMarkdownManager' instance to write out. If, necessary.
    """
    setup_cfg = setup_cfg.resolve()

    cfg = configparser.RawConfigParser(allow_no_value=True, comment_prefixes="/")
    cfg.read(setup_cfg)
    if not cfg.has_section(BUILDER_SECTION_NAME):
        raise MissingSectionException(f"'setup.cfg' is missing {BUILDER_SECTION_NAME}")

    readme_mgr = _build_out_sections(
        cfg,
        setup_cfg.parent,
        github_full_repo,
        base_keywords,
        dirs_exclude,
        repo_license,
        token,
        commit_message,
    )

    # Re-order some sections to the top
    tops = [
        BUILDER_SECTION_NAME,
        "metadata",
        "semantic_release",
        "options",
    ]
    # and any 'options.*' & sort them
    tops.extend(
        sorted(s for s in cfg.sections() if s.startswith("options.") and s not in tops)
    )

    # Build new 'setup.cfg'
    cfg_new = configparser.RawConfigParser(allow_no_value=True)  # no interpolation
    for sec in tops:
        cfg_new[sec] = cfg[sec]
    for sec in cfg.sections():  # add rest of existing sections
        if sec not in tops:
            cfg_new[sec] = cfg[sec]
    with open(setup_cfg, "w") as f:
        cfg_new.write(f)

    # Comment generated sections w/ comments saying so & clean up whitespace
    with open(setup_cfg) as f:
        c = f.read()
        meta_auto_attrs = [
            f.name
            for f in dataclasses.fields(MetadataSection)
            if f.name in cfg_new["metadata"].keys()
        ]
        c = c.replace(
            "[metadata]",
            f"[metadata]  # {GENERATED_STR}: {', '.join(meta_auto_attrs)}",
        )
        c = c.replace(
            "[semantic_release]",
            f"[semantic_release]  # fully-{GENERATED_STR}",
        )
        c = c.replace(
            "[options]",
            f"[options]  # {GENERATED_STR}: python_requires, packages",
        )
        c = c.replace(
            "[options.package_data]",
            f"[options.package_data]  # {GENERATED_STR}: '*'",
        )
        c = c.replace(
            "[options.packages.find]",
            f"[options.packages.find]  # {GENERATED_STR}: include/exclude",
        )
        c = re.sub(r"(\t| )+\n", "\n", c)  # remove trailing whitespace
    with open(setup_cfg, "w") as f:
        f.write(c)

    return readme_mgr


def main(
    setup_cfg: Path,
    github_full_repo: str,
    base_keywords: List[str],
    dirs_exclude: List[str],
    repo_license: str,
    token: str,
    commit_message: str,
) -> None:
    """Read and write all necessary files."""
    # build & write the setup.cfg
    readme_mgr = write_setup_cfg(
        setup_cfg,
        github_full_repo,
        base_keywords,
        dirs_exclude,
        repo_license,
        token,
        commit_message,
    )

    # also, write the readme, if necessary
    if readme_mgr:
        with open(readme_mgr.readme_path, "w") as f:
            for line in readme_mgr.lines:
                f.write(line)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=f"Read/transform 'setup.cfg' and 'README.md' files. "
        f"Builds out 'setup.cfg' sections according to [{BUILDER_SECTION_NAME}].",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "setup_cfg_file",
        type=lambda x: argparse_tools.validate_arg(
            Path(x),
            Path(x).name == "setup.cfg" and Path(x).exists(),
            FileNotFoundError("setup.cfg"),
        ),
        help="path to the 'setup.cfg' file",
    )
    parser.add_argument(
        "github_full_repo",
        type=lambda x: argparse_tools.validate_arg(
            x,
            bool(re.match(r"(\w|-)+/(\w|-)+$", x)),
            ValueError("Not a valid GitHub repo"),
        ),
        help="Fully-named GitHub repo, ex: WIPACrepo/wipac-dev-tools",
    )
    parser.add_argument(
        "--base-keywords",
        nargs="*",
        required=True,
        help="A list of keywords to add to metadata",
    )
    parser.add_argument(
        "--directory-exclude",
        nargs="*",
        required=True,
        help="A list of directories to exclude from release",
    )
    parser.add_argument(
        "--license",
        required=True,
        help="The repo's license type",
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
    args = parser.parse_args()
    logging_tools.log_argparse_args(args, logger=LOGGER, level="WARNING")

    main(
        args.setup_cfg_file,
        args.github_full_repo,
        args.base_keywords,
        args.directory_exclude,
        args.license,
        args.token,
        args.commit_message,
    )
