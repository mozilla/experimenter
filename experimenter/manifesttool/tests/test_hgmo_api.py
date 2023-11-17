from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import responses
from parameterized import parameterized

from manifesttool import hgmo_api
from manifesttool.hgmo_api import HGMO_URL
from manifesttool.repository import Ref


class HgMoApiTests(TestCase):
    """Tests for hg.mozilla.org API wrappers."""

    @parameterized.expand(
        [
            ("tip", "0" * 40),
            ("foo", "1" * 40),
        ]
    )
    @responses.activate
    def test_resolve_branch(self, ref_name: str, resolved: str):
        """Testing get_bookmark_rev."""
        responses.get(
            f"{HGMO_URL}/repo/json-log?rev=bookmark({ref_name})",
            json={
                "node": "bogus",
                "entries": [
                    {
                        "node": resolved,
                    },
                ],
            },
        )

        result = hgmo_api.resolve_branch("repo", ref_name)

        self.assertEqual(result, Ref(ref_name, resolved))

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
