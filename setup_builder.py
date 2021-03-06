"""Module to build `setup.cfg` sections for use by `setup.py`/`setuptools`.

Used in CI/CD, used by GH Action.
"""

import argparse
import configparser
import dataclasses
import enum
import os
import re
from typing import Any, Dict, Iterator, List, Optional, Tuple, cast

import requests

BUILDER_SECTION_NAME = "wipac:cicd_setup_builder"
GENERATED_STR = f"generated by {BUILDER_SECTION_NAME}"
REAMDE_BADGES_START_DELIMITER = "<!--- Top of README Badges (automated) --->"
REAMDE_BADGES_END_DELIMITER = "<!--- End of README Badges (automated) --->"

_PYTHON_MINOR_RELEASE_MAX = 50


class FilenameExtension(enum.Enum):
    """Extensions of a file."""

    DOT_MD = ".md"
    DOT_RST = ".rst"


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

    def __init__(self, github_full_repo: str) -> None:
        self.url = f"https://github.com/{github_full_repo}"

        _json = requests.get(f"https://api.github.com/repos/{github_full_repo}").json()
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
                    "'author' and 'author_email' must be provided when "
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
        keywords = self.keywords_spaced.strip().split() + base_keywords
        if not keywords and self.pypi_name:
            raise Exception(
                "keywords must be provided when 'pypi_name' is given (PyPI-metadata mode)"
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


def long_description_content_type(extension: FilenameExtension) -> str:
    """Return the long_description_content_type for the given file extension (no dot)."""
    try:
        return {
            FilenameExtension.DOT_MD: "text/markdown",
            FilenameExtension.DOT_RST: "text/x-rst",
        }[extension]
    except KeyError:
        return "text/plain"


class FromFiles:
    """Get things that require reading files."""

    def __init__(self, root: str, bsec: BuilderSection) -> None:
        if not os.path.exists(root):
            raise NotADirectoryError(root)
        self._bsec = bsec
        self.root = os.path.abspath(root)
        self.pkg_path = self._get_package_path()
        self.package = os.path.basename(self.pkg_path)
        self.readme, self.readme_ext = self._get_readme_ext()
        self.version = self._get_version()
        self.development_status = self._get_development_status()

    def _get_package_path(self) -> str:
        """Find the package."""

        def _get_packages() -> Iterator[str]:
            """This is essentially [options]'s `packages = find:`."""
            for directory in os.listdir(self.root):
                directory = os.path.join(self.root, directory)
                if not os.path.isdir(directory):
                    continue
                if "__init__.py" in os.listdir(directory):
                    yield directory

        pkgs = [os.path.join(self.root, p) for p in self._bsec.packages()]
        if not pkgs:
            pkgs = list(_get_packages())
        if not pkgs:
            raise Exception(
                f"No package found in '{self.root}'. Are you missing an __init__.py?"
            )
        if len(pkgs) > 1:
            raise Exception(
                f"More than one package found in '{self.root}' ({pkgs}). Remove extra __init__.py files."
            )
        return pkgs[0]

    def _get_readme_ext(self) -> Tuple[str, FilenameExtension]:
        """Return the 'README' file and its extension."""
        for fname in os.listdir(self.root):
            if fname.startswith("README."):
                _, ext = os.path.splitext(fname)
                return fname, FilenameExtension(ext)
        raise Exception(f"No README file found in '{self.root}'")

    def _get_version(self) -> str:
        """Get the package's `__version__` string.

        This is essentially [metadata]'s `version = attr: <module-path to __version__>`.

        `__version__` needs to be parsed as plain text due to potential
        race condition, see:
        https://stackoverflow.com/a/2073599/13156561
        """
        with open(os.path.join(self.pkg_path, "__init__.py"), "r") as f:
            for line in f.readlines():
                if "__version__" in line:
                    # grab "X.Y.Z" from `__version__ = 'X.Y.Z'`
                    # - quote-style insensitive
                    return line.replace('"', "'").split("=")[-1].split("'")[1]

        raise Exception(f"cannot find __version__ in {self.pkg_path}/__init__.py")

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
                f"Could not figure Development Status for version: {self.version}"
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
        with open(ffile.readme, "r") as f:
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
    def readme(self) -> str:
        """Get the README file."""
        return self.ffile.readme

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
    root_path: str,
    github_full_repo: str,
    base_keywords: List[str],
    dirs_exclude: List[str],
    repo_license: str,
) -> Optional[READMEMarkdownManager]:
    """Build out the `[metadata]`, `[semantic_release]`, and `[options]` sections in `cfg`.

    Return a 'READMEMarkdownManager' instance to write out. If, necessary.
    """
    bsec = BuilderSection(**dict(cfg[BUILDER_SECTION_NAME]))  # checks req/extra fields
    ffile = FromFiles(root_path, bsec)  # get things that require reading files
    gh_api = GitHubAPI(github_full_repo)

    # [metadata]
    if not cfg.has_section("metadata"):  # will only override some fields
        cfg["metadata"] = {}
    meta_version = f"attr: {ffile.package}.__version__"  # "wipac_dev_tools.__version__"
    # if we DON'T want PyPI stuff:
    if not bsec.pypi_name:
        cfg["metadata"]["version"] = meta_version
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
            version=meta_version,
            url=gh_api.url,
            author=bsec.author,
            author_email=bsec.author_email,
            description=gh_api.description,
            long_description=f"file: README{ffile.readme_ext.value}",
            long_description_content_type=long_description_content_type(
                ffile.readme_ext
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
        "version_variable": f"{ffile.package}/__init__.py:__version__",  # "wipac_dev_tools/__init__.py:__version__"
        "upload_to_pypi": "True" if bsec.pypi_name else "False",  # >>> str(bool(x))
        "patch_without_tag": "True",
        "commit_parser": "semantic_release.history.tag_parser",
        "minor_tag": "[minor]",
        "fix_tag": "[fix]",
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
        pkgs = bsec.packages()
        cfg["options.packages.find"] = {}
        if pkgs:
            cfg["options.packages.find"]["include"] = list_to_dangling(
                pkgs + [f"{p}.*" for p in pkgs]
            )
        else:
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
    if ffile.readme_ext == FilenameExtension.DOT_MD:
        return READMEMarkdownManager(ffile, github_full_repo, bsec, gh_api)
    return None


class MissingSectionException(Exception):
    """Raise when the wanted section is missing."""


def write_setup_cfg(
    setup_cfg: str,
    github_full_repo: str,
    base_keywords: List[str],
    dirs_exclude: List[str],
    repo_license: str,
) -> Optional[READMEMarkdownManager]:
    """Build/write the `setup.cfg` sections according to `BUILDER_SECTION_NAME`.

    Return a 'READMEMarkdownManager' instance to write out. If, necessary.
    """
    setup_cfg = os.path.abspath(setup_cfg)

    cfg = configparser.RawConfigParser(allow_no_value=True, comment_prefixes="/")
    cfg.read(setup_cfg)
    if not cfg.has_section(BUILDER_SECTION_NAME):
        raise MissingSectionException(f"'setup.cfg' is missing {BUILDER_SECTION_NAME}")

    readme_mgr = _build_out_sections(
        cfg,
        os.path.dirname(setup_cfg),
        github_full_repo,
        base_keywords,
        dirs_exclude,
        repo_license,
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
    with open(setup_cfg, "r") as f:
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
    setup_cfg: str,
    github_full_repo: str,
    base_keywords: List[str],
    dirs_exclude: List[str],
    repo_license: str,
) -> None:
    """Read and write all necessary files."""
    # build & write the setup.cfg
    readme_mgr = write_setup_cfg(
        setup_cfg,
        github_full_repo,
        base_keywords,
        dirs_exclude,
        repo_license,
    )

    # also, write the readme, if necessary
    if readme_mgr:
        with open(readme_mgr.readme, "w") as f:
            for line in readme_mgr.lines:
                f.write(line)


if __name__ == "__main__":

    def _assert_setup_cfg(arg: str) -> str:
        if not (arg.endswith("/setup.cfg") or arg == "setup.cfg"):
            raise ValueError()  # excepted by argparse & formatted nicely
        if not os.path.exists(arg):
            raise FileNotFoundError(arg)
        return arg

    def _assert_github_full_repo(arg: str) -> str:
        if not re.match(r"(\w|-)+/(\w|-)+$", arg):
            raise ValueError()  # excepted by argparse & formatted nicely
        return arg

    parser = argparse.ArgumentParser(
        description=f"Read/transform 'setup.cfg' and 'README.md' files. "
        f"Builds out 'setup.cfg' sections according to [{BUILDER_SECTION_NAME}].",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "setup_cfg_file",
        type=_assert_setup_cfg,
        help="path to the 'setup.cfg' file",
    )
    parser.add_argument(
        "github_full_repo",
        type=_assert_github_full_repo,
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
    args = parser.parse_args()

    main(
        args.setup_cfg_file,
        args.github_full_repo,
        args.base_keywords,
        args.directory_exclude,
        args.license,
    )
