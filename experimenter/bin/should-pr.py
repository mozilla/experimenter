#!/usr/bin/env python

import subprocess
import sys
from pathlib import Path

MANIFEST_DIR = (
    Path(__file__)
    .parent.parent.joinpath("experimenter", "features", "manifests")
    .resolve()
)


def changed_files() -> list[Path]:
    output = subprocess.check_output(["git", "status", "--porcelain"], encoding="utf-8")
    files = [Path(line[3:]) for line in output.splitlines()]
    return files


def is_ref_cache(path: Path):
    return path.name == ".ref-cache.yaml" and path.resolve().is_relative_to(MANIFEST_DIR)


def main() -> int:
    files = [f for f in changed_files() if not is_ref_cache(f)]

    return int(not len(files))


if __name__ == "__main__":
    sys.exit(main())
