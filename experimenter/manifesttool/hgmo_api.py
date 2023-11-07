import os
from pathlib import Path
from typing import Any

import requests

from manifesttool.repository import Ref

HGMO_URL = "https://hg.mozilla.org"


def api_request(path: str, **kwargs) -> dict[str, Any]:
    """Make a request to hg.mozilla.org."""
    return requests.get(f"{HGMO_URL}/{path}", **kwargs).json()


def get_tip_rev(repo: str) -> Ref:
    """Get the revision of the current repository tip.

    Args:
        repo:
            The repository name.
    """
    rsp = api_request(f"{repo}/json-log?rev=tip:tip")
    return Ref("tip", rsp["node"])


def fetch_file(
    repo: str,
    file_path: str,
    rev: str,
    download_path: Path,
):
    url = f"{HGMO_URL}/{repo}/raw-file/{rev}/{file_path}"
    with requests.get(url, stream=True) as req:
        req.raise_for_status()
        with download_path.open("wb") as f:
            for chunk in req.iter_content(chunk_size=8192):
                f.write(chunk)
