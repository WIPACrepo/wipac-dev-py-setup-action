"""Print/return the latest python3 version."""


import logging
from typing import Tuple

import requests

LOGGER = logging.getLogger(__name__)


def get_latest_py3_release() -> Tuple[int, int]:
    """Return the latest python3 release version (supported by GitHub) as
    tuple."""
    url = "https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json"
    LOGGER.info(f"querying {url}")

    manifest = requests.get(url).json()
    manifest = [d for d in manifest if d["stable"]]  # only stable releases

    manifest = sorted(  # sort by version
        manifest,
        key=lambda d: [int(y) for y in d["version"].split(".")],
        reverse=True,
    )

    version = manifest[0]["version"]
    LOGGER.info(f"latest is {version}")

    return int(version.split(".")[0]), int(version.split(".")[1])


if __name__ == "__main__":
    print(f"{'.'.join(str(v) for v in get_latest_py3_release())}")
