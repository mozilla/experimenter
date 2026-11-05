import packaging.version
from django.test import TestCase

from experimenter.experiments.tests import (
    mock_firefox_versions_duplicate_value,
    mock_firefox_versions_invalid_name,
    mock_firefox_versions_invalid_value_format,
    mock_firefox_versions_non_string_value,
    mock_firefox_versions_not_a_mapping,
    mock_valid_firefox_versions,
)
from experimenter.experiments.versions import (
    Version,
    VersionsLoader,
    check_firefox_versions,
)


class VersionTests(TestCase):
    def test_no_version_is_first_with_empty_value(self):
        members = list(Version)
        self.assertEqual(members[0], Version.NO_VERSION)
        self.assertEqual(Version.NO_VERSION.value, "")

    def test_names_are_unique(self):
        names = [member.name for member in Version]
        self.assertEqual(len(names), len(set(names)))

    def test_values_are_unique(self):
        values = [member.value for member in Version]
        self.assertEqual(len(values), len(set(values)))

    def test_legacy_name(self):
        self.assertEqual(Version.FIREFOX_9201.value, "92.0.1")

    def test_beta_name(self):
        self.assertEqual(Version.FIREFOX_156_B3.value, "156.0b3")

    def test_dot_release_name(self):
        self.assertEqual(Version.FIREFOX_140_0_1.value, "140.0.1")

    def test_new_major_present(self):
        self.assertEqual(Version.FIREFOX_166_4_0.value, "166.4.0")

    def test_parse(self):
        self.assertEqual(
            Version.parse("160.!"),
            packaging.version.parse("160.0"),
        )


@mock_valid_firefox_versions
class TestVersionsLoader(TestCase):
    def setUp(self):
        VersionsLoader.clear_cache()

    def tearDown(self):
        VersionsLoader.clear_cache()

    def test_all_loads_the_versions_mapping(self):
        self.assertEqual(
            VersionsLoader.all(),
            {
                "FIREFOX_160": "160.!",
                "FIREFOX_160_0_1": "160.0.1",
                "FIREFOX_160_1_0": "160.1.0",
                "FIREFOX_161_B3": "161.0b3",
            },
        )

    def test_all_is_cached_until_cleared(self):
        self.assertIs(VersionsLoader.all(), VersionsLoader.all())
        cached = VersionsLoader.all()
        VersionsLoader.clear_cache()
        self.assertIsNot(VersionsLoader.all(), cached)


class TestCheckFirefoxVersions(TestCase):
    def setUp(self):
        VersionsLoader.clear_cache()

    def tearDown(self):
        VersionsLoader.clear_cache()

    @mock_valid_firefox_versions
    def test_valid_firefox_versions_do_not_trigger_check_error(self):
        self.assertEqual(check_firefox_versions(None), [])

    def test_committed_firefox_versions_do_not_trigger_check_error(self):
        self.assertEqual(check_firefox_versions(None), [])

    @mock_firefox_versions_not_a_mapping
    def test_versions_not_a_mapping_triggers_check_error(self):
        errors = check_firefox_versions(None)
        self.assertEqual(len(errors), 1)
        self.assertIn("Error loading Firefox Versions", errors[0].msg)

    @mock_firefox_versions_invalid_name
    def test_invalid_name_triggers_check_error(self):
        errors = check_firefox_versions(None)
        self.assertEqual(len(errors), 1)
        self.assertIn("Error loading Firefox Versions", errors[0].msg)

    @mock_firefox_versions_invalid_value_format
    def test_invalid_value_format_triggers_check_error(self):
        errors = check_firefox_versions(None)
        self.assertEqual(len(errors), 1)
        self.assertIn("Error loading Firefox Versions", errors[0].msg)

    @mock_firefox_versions_non_string_value
    def test_non_string_value_triggers_check_error(self):
        errors = check_firefox_versions(None)
        self.assertEqual(len(errors), 1)
        self.assertIn("Error loading Firefox Versions", errors[0].msg)

    @mock_firefox_versions_duplicate_value
    def test_duplicate_value_triggers_check_error(self):
        errors = check_firefox_versions(None)
        self.assertEqual(len(errors), 1)
        self.assertIn("Error loading Firefox Versions", errors[0].msg)
