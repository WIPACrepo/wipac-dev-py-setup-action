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
        dirs_exclude = [d.strip().strip("/") for d in dirs_exclude]

    for directory in [p for p in root_dir.iterdir() if p.is_dir()]:
        if directory.name in dirs_exclude:
            continue
        if is_classical_package(directory):
            yield directory.name


def is_namespace_package(path: Path) -> bool:
    """Return True if the path is a namespace package."""
    if not path.is_dir():
        return False

    return any(f.suffix == ".py" for f in path.iterdir() if f.is_file())


def is_classical_package(path: Path) -> bool:
    """Return True if the path is a classical package."""
    if not path.is_dir():
        return False

    return (path / "__init__.py").exists()
