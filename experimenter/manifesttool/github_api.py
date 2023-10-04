import requests
import os
from typing import Any

GITHUB_API_URL = "https://api.github.com"
GITHUB_API_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

if bearer_token := os.getenv("GITHUB_BEARER_TOKEN"):  # pragma: no cover
    GITHUB_API_HEADERS["Authorization"] = f"Bearer {bearer_token}"


def api_request(path: str, **kwargs: dict[str, Any]) -> dict[str, Any]:
    """Make a request to the GitHub API."""

    return requests.get(
        f"{GITHUB_API_URL}/{path}", headers=GITHUB_API_HEADERS, **kwargs
    ).json()


def get_main_ref(repo: str) -> str:
    """Get the revision of the current main branch of the requested repository.

    Args:
        repo:
            The repository, including the owner.
    """

    rsp = api_request(f"repos/{repo}/branches/main")
    return rsp["commit"]["sha"]
