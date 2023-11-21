from pathlib import Path
from unittest import TestCase
from tempfile import TemporaryDirectory

import yaml

from manifesttool.repository import RefCache


class CacheTests(TestCase):
    def test_load_from_file(self):
        """Testing RefCache.load_from_file."""

        with TemporaryDirectory() as tmp:
            path = Path(tmp, ".ref-cache.yml")

            with path.open("w") as f:
                yaml.safe_dump(
                    {
                        "foo": "foo-target",
                        "bar": "bar-target",
                    },
                    f,
                )

                cache = RefCache.load_from_file(path)

            self.assertEqual(
                cache.__root__,
                {
                    "foo": "foo-target",
                    "bar": "bar-target",
                },
            )

    def test_write_to_file(self):
        """Testing RefCache.write_to_file."""
        cache = RefCache(
            __root__={
                "foo": "foo-target",
                "bar": "bar-target",
            }
        )

        with TemporaryDirectory() as tmp:
            path = Path(tmp, ".ref-cache.yml")
            cache.write_to_file(path)

            with path.open("r") as f:
                read_back = yaml.safe_load(f)

        self.assertEqual(
            read_back,
            {
                "foo": "foo-target",
                "bar": "bar-target",
            },
        )

    def test_load_or_create_not_exists(self):
        """Testing RefCache.load_or_create when the file doesn't exist."""
        with TemporaryDirectory() as tmp:
            path = Path(tmp, ".ref-cache.yml")

            self.assertFalse(path.exists())

            cache = RefCache.load_or_create(path)

            self.assertFalse(path.exists())
            self.assertEqual(cache, RefCache())
