from unittest import TestCase

import responses

from manifesttool import github_api


class GitHubApiTests(TestCase):
    """Tests for GitHub API wrappers."""

    @responses.activate
    def test_get_main_ref(self):
        """Testing get_main_ref."""
        responses.add(
            responses.Response(
                method="GET",
                url="https://api.github.com/repos/owner/repo/branches/main",
                json={
                    "commit": {
                        "sha": "0" * 40,
                    }
                },
            )
        )

        result = github_api.get_main_ref("owner/repo")

        self.assertEqual(result, "0" * 40)
