from unittest import mock

from django.test import TestCase

from experimenter.jetstream.client import get_featmon_slugs


class TestGetFeatmonSlugs(TestCase):
    def setUp(self):
        super().setUp()
        get_featmon_slugs.cache_clear()

    def tearDown(self):
        super().tearDown()
        get_featmon_slugs.cache_clear()

    def test_returns_slugs_from_slug_field(self):
        toml = '[features.my_feature]\nslug = "my-feature"\n'
        with mock.patch("pathlib.Path.read_text", return_value=toml):
            self.assertIn("my-feature", get_featmon_slugs())

    def test_derives_slug_from_key_when_no_slug_field(self):
        toml = "[features.my_feature]\n"
        with mock.patch("pathlib.Path.read_text", return_value=toml):
            self.assertIn("my-feature", get_featmon_slugs())

    def test_returns_empty_frozenset_when_file_not_found(self):
        with mock.patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
            self.assertEqual(get_featmon_slugs(), frozenset())

    def test_returns_empty_frozenset_when_toml_invalid(self):
        import tomllib

        with mock.patch(
            "pathlib.Path.read_text", side_effect=tomllib.TOMLDecodeError
        ):
            self.assertEqual(get_featmon_slugs(), frozenset())

    def test_returns_multiple_slugs(self):
        toml = (
            '[features.feature_a]\nslug = "feature-a"\n'
            '[features.feature_b]\nslug = "feature-b"\n'
        )
        with mock.patch("pathlib.Path.read_text", return_value=toml):
            slugs = get_featmon_slugs()
            self.assertIn("feature-a", slugs)
            self.assertIn("feature-b", slugs)

    def test_result_is_cached(self):
        toml = '[features.my_feature]\nslug = "my-feature"\n'
        with mock.patch("pathlib.Path.read_text", return_value=toml) as mock_read:
            get_featmon_slugs()
            get_featmon_slugs()
            mock_read.assert_called_once()
