"""Print the list of setup/pip extras (options.extras_require section) for a setup.cfg."""


import argparse
import configparser
from pathlib import Path
from typing import Iterator


def iter_extras(setup_cfg_file: Path) -> Iterator[str]:
    """Yield each extra key."""
    cfg = configparser.ConfigParser()
    cfg.read(setup_cfg_file)
    try:
        yield from list(cfg["options.extras_require"].keys())
    except KeyError:
        return


if __name__ == "__main__":

    def _type_setup_cfg(arg: str) -> Path:
        fpath = Path(arg)
        if fpath.name != "setup.cfg":
            raise ValueError()  # excepted by argparse & formatted nicely
        if not fpath.exists():
            raise FileNotFoundError(arg)
        return fpath

    parser = argparse.ArgumentParser(
        description="Read 'setup.cfg' and get the [options.extras_require] section's keys",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "setup_cfg_file",
        type=_type_setup_cfg,
        help="path to the 'setup.cfg' file",
    )
    args = parser.parse_args()

    for extra in iter_extras(args.setup_cfg_file):
        print(extra)
