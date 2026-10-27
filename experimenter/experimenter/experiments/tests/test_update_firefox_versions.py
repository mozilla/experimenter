import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase, override_settings
from parameterized import parameterized
from pydantic import ValidationError

from experimenter.experiments.tests import (
    FIXTURES_PATH,
    mock_manifests_fenix_ahead,
    mock_manifests_non_version_dir,
    mock_manifests_same_major,
)
from experimenter.experiments.versions import VersionsLoader


class UpdateFirefoxVersionsTests(TestCase):
    def setUp(self):
        VersionsLoader.clear_cache()
        self.addCleanup(VersionsLoader.clear_cache)

        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.versions_path = Path(self.temp_dir.name) / "versions.yaml"
        self.override = override_settings(FIREFOX_VERSIONS_PATH=self.versions_path)
        self.override.enable()
        self.addCleanup(self.override.disable)

    def use_versions_fixture(self, name):
        shutil.copy(FIXTURES_PATH / name, self.versions_path)
        VersionsLoader.clear_cache()
        return self.versions_path

    @mock_manifests_same_major
    def test_appends_up_to_ceiling_with_nine_entries_each(self):
        versions_path = self.use_versions_fixture("below_ceiling.yaml")

        call_command("update_firefox_versions")

        self.assertEqual(
            versions_path.read_text(),
            (FIXTURES_PATH / "at_ceiling.yaml").read_text(),
        )

    @mock_manifests_fenix_ahead
    def test_uses_highest_major_across_applications(self):
        versions_path = self.use_versions_fixture("below_ceiling.yaml")

        call_command("update_firefox_versions")

        content = versions_path.read_text()
        self.assertIn('FIREFOX_107_4_0: "107.4.0"', content)
        self.assertNotIn("FIREFOX_108:", content)

    @mock_manifests_same_major
    def test_no_op_at_ceiling(self):
        versions_path = self.use_versions_fixture("at_ceiling.yaml")
        original_content = versions_path.read_text()

        call_command("update_firefox_versions")

        self.assertEqual(versions_path.read_text(), original_content)

    @mock_manifests_same_major
    def test_existing_entries_are_untouched(self):
        versions_path = self.use_versions_fixture("below_ceiling.yaml")
        original_content = versions_path.read_text()

        call_command("update_firefox_versions")

        self.assertTrue(versions_path.read_text().startswith(original_content))

    @mock_manifests_non_version_dir
    def test_non_version_directories_are_ignored(self):
        versions_path = self.use_versions_fixture("below_ceiling.yaml")

        call_command("update_firefox_versions")

        content = versions_path.read_text()
        self.assertIn('FIREFOX_105_4_0: "105.4.0"', content)
        self.assertNotIn("FIREFOX_106:", content)

    @parameterized.expand(
        [
            "not_a_mapping.yaml",
            "invalid_name.yaml",
            "invalid_value_format.yaml",
            "non_string_value.yaml",
            "duplicate_value.yaml",
        ]
    )
    @mock_manifests_same_major
    def test_invalid_versions_file_raises_and_leaves_file_untouched(self, fixture_name):
        versions_path = self.use_versions_fixture(fixture_name)
        original_content = versions_path.read_text()

        with self.assertRaises(ValidationError):
            call_command("update_firefox_versions")

        self.assertEqual(versions_path.read_text(), original_content)
