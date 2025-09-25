"""Tool for finding python packages."""

from pathlib import Path
from typing import Iterator


def iter_packages(
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


def is_classical_package(path: Path) -> bool:
    """Return True if the path is a classical package (has __init__.py)."""
    return path.is_dir() and (path / "__init__.py").exists()


def is_namespace_package(path: Path) -> bool:
    """
    Return True if the path is an implicit namespace package (PEP 420):
    directory with no __init__.py that contains at least one .py file directly.
    """
    if not path.is_dir() or (path / "__init__.py").exists():
        return False

    return any(p.suffix == ".py" for p in path.iterdir() if p.is_file())
