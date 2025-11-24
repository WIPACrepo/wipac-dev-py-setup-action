"""Tool for finding python packages."""

import os
from pathlib import Path
from typing import Iterator


def iter_all_dirs(root_dir: Path) -> Iterator[Path]:
    """Iterate all directories under `root_dir`, including nested ones."""
    for parent, dirs, _ in os.walk(root_dir):
        for d in dirs:
            yield Path(parent) / d


def all_packages(
    root_dir: Path,
    dirs_exclude: list[Path] | None = None,
    include_namespace_packages: bool = False,
    no_subpackages: bool = False,
) -> list[Path]:
    """
    Retrieves all the packages under a given root directory, excluding any
    listed under `dirs_exclude` (whose paths are relative to `root_dir`).

    A package is any directory that has a '__init__.py' file. However, if
    `include_namespace_packages` is True, implicit namespace packages
    (PEP 420) are also included.

    If `no_subpackages` is True, only packages not nested under another
    package are returned.
    """
    if dirs_exclude is None:
        exclude_set: set[Path] = set()
    else:
        exclude_set = {root_dir / d for d in dirs_exclude}

    # recursively find all packages and subpackages
    collected: list[Path] = []
    for dpath in iter_all_dirs(root_dir):
        # exclude whole subtrees
        if any(dpath.is_relative_to(ex_dir) for ex_dir in exclude_set):
            continue

        # package detection
        if is_classical_package(dpath):
            collected.append(dpath)
        elif include_namespace_packages and is_namespace_package(dpath):
            collected.append(dpath)
        else:
            pass  # not a package

    # optionally, don't include any subpackages
    if no_subpackages:
        collected = [
            c
            for c in collected
            # is_relative_to() is self-reflexive, so we must add `c != other` condition
            if not any(c != other and c.is_relative_to(other) for other in collected)
        ]

    return sorted(collected)


def is_classical_package(path: Path) -> bool:
    """Return True if the path is a classical package (has __init__.py)."""
    return path.is_dir() and (path / "__init__.py").exists()


def is_namespace_package(path: Path) -> bool:
    """
    Return True if the path is an implicit namespace package (PEP 420):
    directory with no __init__.py that contains at least one .py file directly.
    """
    if not path.is_dir():
        return False

    if is_classical_package(path):
        return False

    return any(p.suffix == ".py" for p in path.iterdir() if p.is_file())
