"""A tool to add some automation to README.md."""

import argparse
import logging
import re
from pathlib import Path
from typing import Literal

import tomlkit
from wipac_dev_tools import argparse_tools, logging_tools

from pyproject_toml_builder import GitHubAPI

LOGGER = logging.getLogger(__name__)


def strip_out_section(
    lines: list[str], section_start: str, section_end: str
) -> tuple[list[str], list[str]]:
    """Return the lines before and after the section.

    Only the first occurrence of the section is considered.
    """
    before, after = [], []
    current_mode: Literal["before", "in_section", "after"] = "before"

    for line in lines:
        if current_mode == "before":
            if line.strip() == section_start:  # beginning of section
                current_mode = "in_section"
            else:
                before.append(line)
        elif current_mode == "in_section":
            if line.strip() == section_end:  # end of section
                current_mode = "after"
            else:
                pass  # don't keep lines, aka strip
        elif current_mode == "after":
            after.append(line)
        else:
            raise ValueError(f"unknown situation: {current_mode=}, {line=}")

    return before, after


class BadgesAugmenter:
    """Add some automation to README.md."""

    BADGES_START_DELIMITER = "<!--- Top of README Badges (automated) --->"
    BADGES_END_DELIMITER = "<!--- End of README Badges (automated) --->"

    def __init__(
        self,
        readme_path: Path,
        gh_api: GitHubAPI,
        name: str,
        homepage: str,
    ) -> None:
        self.readme_path = readme_path
        self.gh_api = gh_api
        self.name = name
        self.pypi_url = homepage if "pypi.org" in homepage else ""

    def write(self) -> None:
        """Add badges to the top of the README.md."""

        # read and strip out existing badges
        with open(self.readme_path) as f:
            lines = f.readlines()
            if self.BADGES_START_DELIMITER + "\n" not in lines:
                LOGGER.info("No badges found, appending to top of README.md")
                before, after = [], lines
            else:
                LOGGER.info("Badges found, replacing them with new ones")
                before, after = strip_out_section(
                    lines,
                    self.BADGES_START_DELIMITER,
                    self.BADGES_END_DELIMITER,
                )

        # write
        with open(self.readme_path, "w") as f:
            for line in before + self._badges_lines() + after:
                f.write(line)

    def _badges_lines(self) -> list[str]:
        """Create and return the lines used to append to a README.md containing various linked-badges."""
        badges_line = ""

        # PyPI badge
        if self.pypi_url:
            badges_line += (
                f"["
                f"![PyPI](https://img.shields.io/pypi/v/{self.name})"
                f"]"
                f"({self.pypi_url}) "
            )

        # GitHub Release badge
        badges_line += (
            f"["
            f"![GitHub release (latest by date including pre-releases)]"
            f"(https://img.shields.io/github/v/release/{self.gh_api.full_repo}?include_prereleases)"
            f"]"
            f"({self.gh_api.url}) "
        )

        # Python versions
        if self.pypi_url:
            badges_line += (
                f"["
                f"![Versions](https://img.shields.io/pypi/pyversions/{self.name}.svg)"
                f"]"
                f"({self.pypi_url}) "
            )

        # PYPI License badge
        if self.pypi_url:
            badges_line += (
                f"["
                f"![PyPI - License](https://img.shields.io/pypi/l/{self.name})"
                f"]"
                f"({self.gh_api.url}/blob/{self.gh_api.default_branch}/LICENSE) "
            )

        # Other GitHub badges
        badges_line += (
            f"["
            f"![GitHub issues](https://img.shields.io/github/issues/{self.gh_api.full_repo})"
            f"]"
            f"({self.gh_api.url}/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aopen) "
        )
        badges_line += (
            f"["
            f"![GitHub pull requests](https://img.shields.io/github/issues-pr/{self.gh_api.full_repo})"
            f"]"
            f"({self.gh_api.url}/pulls?q=is%3Apr+sort%3Aupdated-desc+is%3Aopen) "
        )

        return [
            self.BADGES_START_DELIMITER,
            "\n",
            badges_line.strip(),  # remove trailing whitespace
            "\n",
            self.BADGES_END_DELIMITER,
            "\n",  # only one newline here, otherwise we get an infinite commit-loop
        ]


def main() -> None:
    """Read and write all necessary files."""
    parser = argparse.ArgumentParser(
        description="Transform 'README.md' file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--readme",
        type=lambda x: argparse_tools.validate_arg(
            Path(x),
            Path(x).name == "README.md",
            ValueError("file needs to be named 'README.md'"),
        ),
        required=True,
        help="path to the 'pyproject.toml' file",
    )
    parser.add_argument(
        "--pyproject-toml",
        type=lambda x: argparse_tools.validate_arg(
            Path(x),
            Path(x).name == "pyproject.toml",
            ValueError("file needs to be named 'pyproject.toml'"),
        ),
        required=True,
        help="path to the 'pyproject.toml' file",
    )
    parser.add_argument(
        "--gh-full-repo",
        type=lambda x: argparse_tools.validate_arg(
            x,
            bool(re.match(r"(\w|-)+/(\w|-)+$", x)),
            ValueError("Not a valid GitHub repo"),
        ),
        required=True,
        help="Fully-named GitHub repo, ex: WIPACrepo/wipac-dev-tools",
    )
    parser.add_argument(
        "--gh-token",
        required=True,
        help="A github token, usually GITHUB_TOKEN",
    )
    args = parser.parse_args()
    logging_tools.set_level("DEBUG", LOGGER)
    logging_tools.log_argparse_args(args, logger=LOGGER)

    with open(args.pyproject_toml) as f:
        pyproject_toml_dict = tomlkit.load(f).unwrap()

    gh_api = GitHubAPI(args.gh_full_repo, args.gh_token)

    # TODO - just read from the pyproject.toml? -- separate from GHA
    # # <name> — `<full_repo>`
    # # lta — `WIPACRepo/lta`
    # <description>
    # yada yada yada
    #
    # ### keywords
    # <comma-separated list of keywords>
    #
    # ### authors
    # <comma-separated list of authors>

    # write badges
    ba = BadgesAugmenter(
        args.readme,
        gh_api,
        pyproject_toml_dict["project"]["name"],
        pyproject_toml_dict["project"]["urls"]["Homepage"],
    )
    ba.write()


if __name__ == "__main__":
    main()
    LOGGER.info("Done.")
