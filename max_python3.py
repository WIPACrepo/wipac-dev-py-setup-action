"""Print/return the max supported python3 release."""


import argparse
import logging

import semantic_version  # type: ignore[import-untyped]

import latest_python3

LOGGER = logging.getLogger(__name__)


def get_max_python(semvar_range: str) -> str:
    """Get the max supported python3 release."""
    spec = semantic_version.SimpleSpec(semvar_range.replace(" ", ""))
    LOGGER.info(f"getting the max supported python3 release for {spec}")

    latest_py3_minor = latest_python3.get_latest_py3_release()[1]

    maxo = max(
        spec.filter(
            semantic_version.Version(f"3.{i}.0") for i in range(latest_py3_minor + 1)
        )
    )

    ret = f"{maxo.major}.{maxo.minor}"
    LOGGER.info(f"max is {ret}")
    return ret


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Print the max supported python3 release",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "semvar-range",
        help="the semantic version range",
    )
    args = parser.parse_args()

    print(get_max_python(args.semvar_range))
