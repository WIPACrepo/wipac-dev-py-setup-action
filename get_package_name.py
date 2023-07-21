"""Print the package name (metadata section) for a setup.cfg."""


import argparse
import configparser
from pathlib import Path


def get_name(setup_cfg_file: Path) -> str:
    """Get package name."""
    cfg = configparser.ConfigParser()
    cfg.read(setup_cfg_file)
    try:
        return cfg["metadata"]["name"]
    except KeyError:
        return "UNKNOWN"


if __name__ == "__main__":

    def _type_setup_cfg(arg: str) -> Path:
        fpath = Path(arg)
        if fpath.name != "setup.cfg":
            raise ValueError()  # excepted by argparse & formatted nicely
        if not fpath.exists():
            raise FileNotFoundError(arg)
        return fpath

    parser = argparse.ArgumentParser(
        description="Read 'setup.cfg' and get the [metadata.name] field",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "setup_cfg_file",
        type=_type_setup_cfg,
        help="path to the 'setup.cfg' file",
    )
    args = parser.parse_args()

    name = get_name(args.setup_cfg_file)
    print(name)
