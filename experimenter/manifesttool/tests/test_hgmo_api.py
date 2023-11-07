from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase

import responses

from manifesttool import hgmo_api
from manifesttool.repository import Ref


class HgMoApiTests(TestCase):
    """Tests for hg.mozilla.org API wrappers."""

    @responses.activate
    def test_get_tip_rev(self):
        """Testing get_tip_rev."""
        responses.add(
            responses.Response(
                method="GET",
                url="https://hg.mozilla.org/repo/json-log?rev=tip:tip",
                json={
                    "node": "0" * 40,
                },
            )
        )

        result = hgmo_api.get_tip_rev("repo")

        self.assertEqual(result, Ref("tip", "0" * 40))

    @responses.activate
    def test_fetch_file(self):
        """Testing fetch_file."""
        responses.add(
            responses.Response(
                method="GET",
                url="https://hg.mozilla.org/repo/raw-file/rev/file/path.txt",
                body=b"hello world\n",
            )
        )

        with NamedTemporaryFile() as temp:
            temp_path = Path(temp.name)
            hgmo_api.fetch_file(
                "repo",
                "file/path.txt",
                "rev",
                temp_path,
            )

            self.assertTrue(temp_path.exists())

            with temp_path.open("rb") as f:
                content = f.read()

            self.assertEqual(content, b"hello world\n")
