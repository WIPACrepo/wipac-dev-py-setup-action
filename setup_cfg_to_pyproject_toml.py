"""A script to migrate a setup.cfg file to a pyproject.toml file.

Only migrates what's needed for running with this GHA package.
"""

import argparse
from configparser import ConfigParser
from pathlib import Path

import tomlkit


def migrate_dependencies(setup_cfg: Path) -> str:
    """Return the setup.cfg's dependencies as a pyproject.toml string with multiline arrays."""
    parser = ConfigParser()
    parser.read_string(setup_cfg.read_text())

    pyproject = tomlkit.document()
    pyproject.add(tomlkit.comment("Generated from setup.cfg dependencies"))

    project = tomlkit.table()

    # [project.dependencies]
    if "options" in parser and "install_requires" in parser["options"]:
        deps = [
            line.strip()
            for line in parser["options"]["install_requires"].splitlines()
            if line.strip()
        ]
        deps_array = tomlkit.array()
        deps_array.multiline(True)
        for dep in deps:
            deps_array.append(dep)
        project["dependencies"] = deps_array

    # [project.optional-dependencies]
    if "options.extras_require" in parser:
        extras = tomlkit.table()
        for extra, deps_block in parser["options.extras_require"].items():
            deps = [line.strip() for line in deps_block.splitlines() if line.strip()]
            deps_array = tomlkit.array()
            deps_array.multiline(True)
            for dep in deps:
                deps_array.append(dep)
            extras[extra] = deps_array
        project["optional-dependencies"] = extras

    pyproject["project"] = project
    return tomlkit.dumps(pyproject)


def _empty_pyproject_toml(x: str) -> Path:
    fpath = Path(x)
    if fpath.name != "pyproject.toml":
        raise RuntimeError(f"{fpath} is not a pyproject.toml file.")
    elif not fpath.exists():
        raise FileNotFoundError(x)
    elif not fpath.is_file():
        raise RuntimeError(f"{fpath} is not a file")
    elif fpath.stat().st_size != 0:
        raise RuntimeError(f"{fpath} is not empty")
    else:
        return fpath


def _setup_cfg(x: str) -> Path:
    fpath = Path(x)
    if fpath.name != "setup.cfg":
        raise RuntimeError(f"{fpath} is not a setup.cfg file.")
    else:
        return fpath


def main():
    parser = argparse.ArgumentParser(description="Migrate setup.cfg to pyproject.toml")
    parser.add_argument(
        "setup_cfg",
        type=_setup_cfg,
        help="Path to setup.cfg input file",
    )
    parser.add_argument(
        "pyproject_toml",
        type=_empty_pyproject_toml,
        help="Path to empty pyproject.toml output file",
    )
    args = parser.parse_args()

    # there never was a setup.cfg, probably a brand new project
    if not args.setup_cfg.exists():
        with args.pyproject_toml.open("a") as f:
            f.write("# pyproject.toml\n")
            f.write("\n")
            # add most likely needed fields
            f.write("[project]\n")
            f.write("dependencies = []  # leave empty if there are no dependencies\n")
            f.write("\n")
            f.write("# optional sections:\n")
            f.write("\n")
            f.write("# [project.optional-dependencies]\n")
            f.write("# foo = []\n")
            f.write("# bar = []\n")
        return

    # header
    args.pyproject_toml.write_text("# pyproject.toml\n")

    # migrate dependencies
    toml_deps_text = migrate_dependencies(args.setup_cfg)
    with args.pyproject_toml.open("a") as f:
        f.write("\n")
        f.write(toml_deps_text)


if __name__ == "__main__":
    main()
