import os
from pathlib import Path
from typing import Any, Generator, Optional, overload

import requests

from manifesttool import download
from manifesttool.repository import Ref

GITHUB_API_URL = "https://api.github.com"
GITHUB_API_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

if bearer_token := os.getenv("GITHUB_BEARER_TOKEN"):  # pragma: no cover
    GITHUB_API_HEADERS["Authorization"] = f"Bearer {bearer_token}"


def api_request(
    path: str, *, raise_for_status: bool = True, **kwargs: dict[str, Any]
) -> requests.Response:
    """Make a request to the GitHub API."""
    url = f"{GITHUB_API_URL}/{path}"
    rsp = requests.get(url, headers=GITHUB_API_HEADERS, **kwargs)

    if rsp.status_code == 403:
        if rsp.headers.get("X-RateLimit-Remaining") == "0":
            raise Exception(f"Could not fetch {url}: GitHub API rate limit exceeded")

    if raise_for_status:
        rsp.raise_for_status()

    return rsp


def paginated_api_request(path: str, per_page: int = 100) -> Generator[Any, None, None]:
    """Make several reqeusts to a paginated API resource and yield each page of results."""
    page = 1

    while True:
        results = api_request(path, params={"page": page, "per_page": per_page}).json()

        # When there are no more results, the API returns an empty list.
        if results:
            yield results
        else:
            break

        page += 1


def resolve_branch(repo: str, branch: str) -> Ref:
    """Get the revision of the current main branch of the requested repository.

    Args:
        repo:
            The repository, including the owner.

        branch:
            The name of the branch.
    """
    rsp = api_request(f"repos/{repo}/branches/{branch}").json()
    return Ref(branch, rsp["commit"]["sha"])


def get_branches(repo: str) -> list[Ref]:
    """Return all the branches in a repository."""
    return _get_refs(repo, "branches")


def get_tags(repo: str) -> list[Ref]:
    """Return all the tags in a repository."""
    return _get_refs(repo, "tags")


def _get_refs(repo: str, kind: str) -> list[Ref]:
    """Return all the refs of a given kind.

    Args:
        repo: The name of the repository, including the owner.
        kind: Either ``"branches"`` or ``"tags"``.

    Returns:
        The list of refs.
    """
    return [
        Ref(ref["name"], ref["commit"]["sha"])
        for page in paginated_api_request(f"repos/{repo}/{kind}")
        for ref in page
    ]


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
    rsp = api_request(
        f"repos/{repo}/contents/{file_path}",
        raise_for_status=False,
        params={"ref": rev},
    )

    rsp.raise_for_status()

    url = rsp.json()["download_url"]

    if download_path is None:
        return download.as_text(url)

    download.to_path(url, download_path)
    return None


def file_exists(repo: str, file_path: str, rev: str) -> bool:
    """Return whether or not a file with the given path exists in the repo at
    the given revision.
    """
    rsp = api_request(
        f"repos/{repo}/contents/{file_path}",
        raise_for_status=False,
        params={"ref": rev},
    )

    if rsp.status_code == 404:
        return False

    rsp.raise_for_status()

    return True
