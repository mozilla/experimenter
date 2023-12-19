from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import TestCase

import responses
from responses import matchers

from manifesttool import github_api
from manifesttool.github_api import GITHUB_API_URL
from manifesttool.repository import Ref

GITHUB_RAW_URL = "https://raw.githubusercontent.com"


def _add_paginated_responses(
    url: str,
    pages: dict[str, dict[str, Any]],
) -> dict[str, responses.Response]:
    return {
        page_number: responses.get(
            url,
            **page_kwargs,
            match=[
                matchers.query_param_matcher({"page": page_number}, strict_match=False),
            ],
        )
        for page_number, page_kwargs in pages.items()
    }


def make_responses_for_fetch(
    repo_name: str, ref: str, path: str, content: bytes
) -> list[responses.Response]:
    download_url = f"{GITHUB_RAW_URL}/{repo_name}/{ref}/{path}"

    return [
        responses.get(
            f"{GITHUB_API_URL}/repos/{repo_name}/contents/{path}",
            match=[matchers.query_param_matcher({"ref": ref})],
            json={
                "download_url": download_url,
            },
        ),
        responses.get(download_url, body=content),
    ]


class GitHubApiTests(TestCase):
    """Tests for GitHub API wrappers."""

    @responses.activate
    def test_resolve_branch(self):
        """Testing resolve_branch."""
        responses.get(
            f"{GITHUB_API_URL}/repos/owner/repo/branches/main",
            json={
                "commit": {
                    "sha": "0" * 40,
                }
            },
        )

        result = github_api.resolve_branch("owner/repo", "main")

        self.assertEqual(result, Ref("main", "0" * 40))

    @responses.activate
    def test_api_limit(self):
        """Testing detection of API rate limit errors."""
        responses.get(
            f"{GITHUB_API_URL}/repos/owner/repo/branches/main",
            headers={
                "X-RateLimit-Remaining": "0",
            },
            status=403,
            body="do not try to json parse this",
        )
        with self.assertRaisesRegex(Exception, "GitHub API rate limit exceeded") as e:
            github_api.resolve_branch("owner/repo", "main")

    @responses.activate
    def test_get_branches(self):
        """Testing get_branches and the underlying paginated_api_request."""
        rsps = _add_paginated_responses(
            f"{GITHUB_API_URL}/repos/owner/repo/branches",
            {
                "1": {
                    "json": [
                        {
                            "name": "main",
                            "commit": {"sha": "0" * 40},
                        }
                    ],
                },
                "2": {
                    "json": [
                        {
                            "name": "foo",
                            "commit": {"sha": "1" * 40},
                        }
                    ]
                },
                "3": {
                    "json": [],
                },
                "4": {
                    "body": Exception("should not be requested"),
                    "status": 400,
                },
            },
        )

        result = github_api.get_branches("owner/repo")
        self.assertEqual(
            result,
            [
                Ref("main", "0" * 40),
                Ref("foo", "1" * 40),
            ],
        )

        self.assertEqual(rsps["1"].call_count, 1)
        self.assertEqual(rsps["2"].call_count, 1)
        self.assertEqual(rsps["3"].call_count, 1)
        self.assertEqual(rsps["4"].call_count, 0)

    @responses.activate
    def test_get_tags(self):
        """Testing get_tags."""
        rsps = _add_paginated_responses(
            f"{GITHUB_API_URL}/repos/owner/repo/tags",
            {
                "1": {
                    "json": [
                        {
                            "name": "tag-1",
                            "commit": {"sha": "0" * 40},
                        }
                    ]
                },
                "2": {
                    "json": [
                        {
                            "name": "tag-2",
                            "commit": {
                                "sha": "1" * 40,
                            },
                        },
                        {
                            "name": "tag-3",
                            "commit": {
                                "sha": "2" * 40,
                            },
                        },
                    ]
                },
                "3": {
                    "json": [],
                },
                "4": {
                    "body": Exception("should not be requested"),
                    "status": 400,
                },
            },
        )

        result = github_api.get_tags("owner/repo")
        self.assertEqual(
            result,
            [
                Ref("tag-1", "0" * 40),
                Ref("tag-2", "1" * 40),
                Ref("tag-3", "2" * 40),
            ],
        )

        self.assertEqual(rsps["1"].call_count, 1)
        self.assertEqual(rsps["2"].call_count, 1)
        self.assertEqual(rsps["3"].call_count, 1)
        self.assertEqual(rsps["4"].call_count, 0)

    @responses.activate
    def test_fetch_file_download(self):
        """Testing github_api.fetch_file."""
        api_rsp, file_rsp = make_responses_for_fetch(
            "repo", "ref", "file/path.txt", b"hello, world\n"
        )

        with TemporaryDirectory() as tmp_dir:
            tmp_filename = Path(tmp_dir, "file.txt")

            github_api.fetch_file("repo", "file/path.txt", "ref", tmp_filename)

            self.assertTrue(tmp_filename.exists())

            with tmp_filename.open("rb") as f:
                contents = f.read()

            self.assertEqual(contents, b"hello, world\n")

        self.assertEqual(api_rsp.call_count, 1)
        self.assertEqual(file_rsp.call_count, 1)

        contents = github_api.fetch_file("repo", "file/path.txt", "ref")
        self.assertEqual(contents, "hello, world\n")

    @responses.activate
    def test_file_exists(self):
        """Testing github_api.file_exists."""
        responses.get(
            f"{GITHUB_API_URL}/repos/repo/contents/file.txt",
            status=404,
            body="404",
            match=[matchers.query_param_matcher({"ref": "foo"})],
        )

        responses.get(
            f"{GITHUB_API_URL}/repos/repo/contents/file.txt",
            json={},
            match=[matchers.query_param_matcher({"ref": "bar"})],
        )

        self.assertFalse(github_api.file_exists("repo", "file.txt", "foo"))
        self.assertTrue(github_api.file_exists("repo", "file.txt", "bar"))
