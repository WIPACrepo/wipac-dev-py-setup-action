#!/usr/bin/env python3
"""
Ensure a dependabot.yml exists and contains canonical pip & GitHub Actions entries.
Other update objects are preserved. Always creates/updates the file.
Uses PyYAML (no ruamel.yaml dependency).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

CANON_PIP: Dict[str, Any] = {
    "package-ecosystem": "pip",
    "directory": "/",
    "schedule": {"interval": "weekly"},
}
CANON_GHA: Dict[str, Any] = {
    "package-ecosystem": "github-actions",
    "directory": "/",
    "schedule": {"interval": "weekly"},
}


def load_or_init(dep_file: Path) -> dict:
    """Load YAML or return minimal structure."""
    if not dep_file.exists():
        dep_file.parent.mkdir(parents=True, exist_ok=True)
        return {"version": 2, "updates": []}

    with dep_file.open("r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error parsing {dep_file}: {e}", file=sys.stderr)
            sys.exit(1)

    if not isinstance(data, dict):
        data = {}
    if data.get("version") != 2:
        data["version"] = 2
    if not isinstance(data.get("updates"), list):
        data["updates"] = []
    return data


def upsert_exact(doc: dict, desired: dict) -> None:
    """Replace or add the update object for a given package-ecosystem."""
    updates: List[dict] = doc["updates"]
    for i, obj in enumerate(updates):
        if (
            isinstance(obj, dict)
            and obj.get("package-ecosystem") == desired["package-ecosystem"]
            and obj.get("directory") == desired["directory"]
        ):
            updates[i] = desired
            return
    updates.append(desired)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ensure dependabot.yml exists and has canonical pip & GitHub Actions entries."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to dependabot.yml (e.g., .github/dependabot.yml)",
    )
    args = parser.parse_args()

    doc = load_or_init(args.path)
    upsert_exact(doc, CANON_PIP)
    upsert_exact(doc, CANON_GHA)

    with args.path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, sort_keys=False)

    print(f"✅ Ensured canonical pip & github-actions entries in {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
