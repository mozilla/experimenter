from pathlib import Path
from typing import Any, Optional, overload

import requests

from manifesttool import download
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


@overload
def fetch_file(repo: str, file_path: str, rev: str) -> str:
    ...  # pragma: no cover


@overload
def fetch_file(repo: str, file_path: str, rev: str, download_path: Path) -> None:
    ...  # pragma: no cover


def fetch_file(
    repo: str,
    file_path: str,
    rev: str,
    download_path: Optional[Path] = None,
):
    """Fetch the file path at the given revision from the repository.

    Args:
        repo:
            The name of the repository.

        file_path:
            The path to the file in the repository.

        rev:
            The revision at which the file is to be fetched.

        download_path:
            If provided, the file will be written to disk at this location.

    Returns:
        If ``download_path`` is ``None``, the file contents are returned as a
        ``str``. Otherwise, ``None`` is returned.
    """
    url = f"{HGMO_URL}/{repo}/raw-file/{rev}/{file_path}"

    if download_path is None:
        return download.as_text(url)

    download.to_path(url, download_path)
    return None
