from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import responses

from manifesttool import hgmo_api
from manifesttool.hgmo_api import HGMO_URL
from manifesttool.repository import Ref


class HgMoApiTests(TestCase):
    """Tests for hg.mozilla.org API wrappers."""

    @responses.activate
    def test_get_tip_rev(self):
        """Testing get_tip_rev."""
        responses.get(
            f"{HGMO_URL}/repo/json-log?rev=tip:tip",
            json={
                "node": "0" * 40,
            },
        )

        result = hgmo_api.get_tip_rev("repo")

        self.assertEqual(result, Ref("tip", "0" * 40))

    @responses.activate
    def test_fetch_file(self):
        """Testing fetch_file."""
        responses.get(
            f"{HGMO_URL}/repo/raw-file/rev/file/path.txt",
            body=b"hello, world\n",
        )

        with TemporaryDirectory() as tmp_dir:
            tmp_filename = Path(tmp_dir, "file.txt")
            hgmo_api.fetch_file("repo", "file/path.txt", "rev", tmp_filename)

            self.assertTrue(tmp_filename.exists())

            with tmp_filename.open("rb") as f:
                content = f.read()

            self.assertEqual(content, b"hello, world\n")

        contents = hgmo_api.fetch_file("repo", "file/path.txt", "rev")
        self.assertEqual(contents, "hello, world\n")
