"""A tool to add some automation to README.md."""

import argparse
import logging
import re
from collections import OrderedDict
from pathlib import Path
from typing import Literal

import tomlkit
from wipac_dev_tools import argparse_tools, logging_tools

from pyproject_toml_builder import GitHubAPI

LOGGER = logging.getLogger(__name__)


def remove_section(
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


class MetadataSectionAugmenter:
    """Automation to add/maintain a metadata section in README.md."""

    START_DELIMITER = "<!--- Top of README Metadata Section (automated) --->"
    END_DELIMITER = "<!--- End of README Metadata Section (automated) --->"

    def __init__(
        self,
        gh_api: GitHubAPI,
        name: str,
        keywords: list[str],
        authors: list[dict[str, str]],
        urls: dict[str, str],
    ) -> None:
        self.gh_api = gh_api
        self.name = name
        self.keywords = keywords
        self.authors = authors
        self.urls = urls

        self.add_description = True

    def _get_insertion_index(self, lines: list[str]) -> int:
        """Return the index of where to insert the metadata section."""

        # plan A: find the first header line, and insert right after it (more or less)
        for i, ln in enumerate(lines):
            # find the first header line
            if ln.startswith("#"):
                index = i + 1
                LOGGER.info(
                    f"No automated metadata section found, inserting after the first header {index=}"
                )
                # now, we need to find the insertion point
                # -- skip blank lines and skip comments
                while lines[index].strip() == "" or lines[index].startswith("<!"):
                    index += 1
                # if this line is not a header, then its the user's description -- keep it
                if not lines[index].startswith("#"):
                    if lines[index] == self.gh_api.description.strip() + "\n":
                        self.add_description = False
                    index += 1  # pick the following line as the insertion point
                # all done
                return index

        # plan B: if we didn't find a header, insert right after badges
        try:
            index = lines.index(BadgesAugmenter.END_DELIMITER + "\n") + 1
            LOGGER.info(
                f"No automated metadata section found, inserting right after badges {index=}"
            )
            return index
        except ValueError:
            pass

        # plan C: insert at top of the file
        LOGGER.info(
            "No automated metadata section found, inserting at top of README.md"
        )
        return 0

    def write(self, readme_path: Path) -> None:
        """Write the metadata section."""

        # read and strip out existing auto metadata section
        with open(readme_path) as f:
            lines = f.readlines()
            if self.START_DELIMITER + "\n" not in lines:  # aka no metadata section
                index = self._get_insertion_index(lines)
                before, after = lines[:index], lines[index:]
            else:
                LOGGER.info("Metadata section found, replacing it with a new one")
                before, after = remove_section(
                    lines,
                    self.START_DELIMITER,
                    self.END_DELIMITER,
                )

        # assemble the metadata section
        section = [
            self.START_DELIMITER,
            "\n\n",
            "<!--- note: this information is pulled from the pyproject.toml --->",
            "\n\n",
            self._details_listings(),
            "\n<br>\n",  # extra line break
            self.END_DELIMITER,
            "\n",  # only one newline here, otherwise we get an infinite commit-loop
        ]

        # write
        with open(readme_path, "w") as f:
            for line in before + section + after:
                f.write(line)

    def _details_listings(self) -> str:
        """Create a mapping of details to add to the metadata section."""
        details: OrderedDict[str, str] = OrderedDict()

        def _get_author_string(entry: dict[str, str]) -> str:
            parts: list[str] = []
            if "name" in entry:
                parts.append(entry["name"])
            if "email" in entry:
                parts.append(f"<a href='mailto:{entry['email']}'>{entry['email']}</a>")
            return " / ".join(parts)

        dotty = "&nbsp;&nbsp;·&nbsp;&nbsp;"  # equivalent to "  ·  " (use for spacing)

        if self.add_description and self.gh_api.description:
            details["Project Description"] = self.gh_api.description.strip()

        if self.authors:
            details["Authors"] = dotty.join(_get_author_string(a) for a in self.authors)

        if self.keywords:
            details["Keywords"] = dotty.join(self.keywords)

        if self.urls:
            details["URLs"] = dotty.join(
                f"<a href='{v}'>{k}</a>" for k, v in self.urls.items()
            )

        # render in html
        if not details:
            return ""
        else:
            rows = []
            for k, v in details.items():
                rows.append(f"    <dt><sub>{k}</sub></dt>\n")  # 'sub' makes text small
                rows.append(f"    <dd><sub>{v}</sub></dd>\n")  # 'sub' makes text small
            return "<dl>\n" + "".join(rows) + "</dl>\n"


class BadgesAugmenter:
    """Automation to add/maintain badges in README.md."""

    START_DELIMITER = "<!--- Top of README Badges (automated) --->"
    END_DELIMITER = "<!--- End of README Badges (automated) --->"

    def __init__(
        self,
        gh_api: GitHubAPI,
        name: str,
        homepage: str,
    ) -> None:
        self.gh_api = gh_api
        self.name = name
        self.pypi_url = homepage if "pypi.org" in homepage else ""

    def write(self, readme_path: Path) -> None:
        """Write the badges."""

        # read and strip out existing badges
        with open(readme_path) as f:
            lines = f.readlines()
            if self.START_DELIMITER + "\n" not in lines:
                LOGGER.info("No badges found, appending to top of README.md")
                before, after = [], lines
            else:
                LOGGER.info("Badges found, replacing them with new ones")
                before, after = remove_section(
                    lines,
                    self.START_DELIMITER,
                    self.END_DELIMITER,
                )

        section = [
            self.START_DELIMITER,
            "\n",
            self._badges_line().strip(),  # remove trailing whitespace
            "\n",
            self.END_DELIMITER,
            "\n",  # only one newline here, otherwise we get an infinite commit-loop
        ]

        # write
        with open(readme_path, "w") as f:
            for line in before + section + after:
                f.write(line)

    def _badges_line(self) -> str:
        """Create and return the line containing various linked-badges."""
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

        return badges_line


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

    ha = MetadataSectionAugmenter(
        gh_api,
        pyproject_toml_dict["project"]["name"],
        pyproject_toml_dict["project"]["keywords"],
        pyproject_toml_dict["project"]["authors"],
        pyproject_toml_dict["project"]["urls"],
    )
    ha.write(args.readme)

    ba = BadgesAugmenter(
        gh_api,
        pyproject_toml_dict["project"]["name"],
        pyproject_toml_dict["project"]["urls"]["Homepage"],
    )
    ba.write(args.readme)


if __name__ == "__main__":
    main()
    LOGGER.info("Done.")
