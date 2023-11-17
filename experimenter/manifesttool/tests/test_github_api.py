from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import TestCase

import responses
from responses import matchers

from manifesttool import github_api
from manifesttool.github_api import GITHUB_RAW_URL
from manifesttool.repository import Ref


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


class GitHubApiTests(TestCase):
    """Tests for GitHub API wrappers."""

    @responses.activate
    def test_resolve_branch(self):
        """Testing resolve_branch."""
        responses.get(
            "https://api.github.com/repos/owner/repo/branches/main",
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
            "https://api.github.com/repos/owner/repo/branches/main",
            headers={
                "X-RateLimit-Remaining": "0",
            },
            status=403,
            body="do not try to json parse this",
        )
        with self.assertRaises(Exception) as e:
            github_api.resolve_branch("owner/repo")
            self.assertIn("GitHub API rate limit exceeded", str(e))

    @responses.activate
    def test_get_branches(self):
        """Testing get_branches and the underlying paginated_api_request."""
        rsps = _add_paginated_responses(
            "https://api.github.com/repos/owner/repo/branches",
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
            "https://api.github.com/repos/owner/repo/tags",
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
        responses.get(f"{GITHUB_RAW_URL}/repo/ref/file/path.txt", body=b"hello, world\n")

        with TemporaryDirectory() as tmp_dir:
            tmp_filename = Path(tmp_dir, "file.txt")

            github_api.fetch_file("repo", "file/path.txt", "ref", tmp_filename)

            self.assertTrue(tmp_filename.exists())

            with tmp_filename.open("rb") as f:
                contents = f.read()

            self.assertEqual(contents, b"hello, world\n")

        contents = github_api.fetch_file("repo", "file/path.txt", "ref")
        self.assertEqual(contents, "hello, world\n")
