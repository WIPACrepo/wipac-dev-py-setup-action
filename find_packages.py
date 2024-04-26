"""Tool for finding python packages."""

from pathlib import Path
from typing import Iterator


def iterate_dirnames(
    root_dir: Path,
    dirs_exclude: list[str] | None = None,
) -> Iterator[str]:
    """This is essentially [options]'s `packages = find:`."""
    if dirs_exclude is None:
        dirs_exclude = []
    else:
        dirs_exclude = [d.split().split("/") for d in dirs_exclude]  # type: ignore

    for directory in [p for p in root_dir.iterdir() if p.is_dir()]:
        if directory.name in dirs_exclude:
            continue
        if "__init__.py" in [p.name for p in directory.iterdir()]:
            yield directory.name
