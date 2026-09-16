import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.test import TestCase, override_settings

from experimenter.addons import (
    NEWTAB_ADDON,
    VERSIONS_FILENAME,
    Addons,
    AddonVersions,
    check_addon_versions,
)
from experimenter.addons.tests import (
    mock_invalid_addon_versions,
    mock_missing_addon_versions,
    mock_multiple_addon_versions,
    mock_valid_addon_versions,
)


@mock_valid_addon_versions
class TestAddons(TestCase):
    def setUp(self):
        Addons.clear_cache()

    def tearDown(self):
        Addons.clear_cache()

    def test_all_loads_every_addon_directory(self):
        self.assertEqual(list(Addons.all()), [NEWTAB_ADDON])

    def test_by_addon_returns_versions(self):
        versions = Addons.by_addon(NEWTAB_ADDON)
        self.assertEqual(
            [version.version for version in versions],
            ["158.0.20260913.220257", "145.0.20250919.173227"],
        )
        self.assertEqual(versions[0].shipit_release, "newtab-158.0.0-build1")
        self.assertEqual(
            versions[0].xpi_revision,
            "9779d0c588762208f33a82c9fc710f81466f6e9e",
        )
        self.assertEqual(versions[0].created.year, 2026)

    def test_by_addon_returns_empty_list_for_unknown_addon(self):
        self.assertEqual(Addons.by_addon("tabtweak"), [])

    def test_sort_key_orders_by_numeric_version_parts(self):
        versions = sorted(Addons.by_addon(NEWTAB_ADDON), key=lambda v: v.sort_key)
        self.assertEqual(
            [version.version for version in versions],
            ["145.0.20250919.173227", "158.0.20260913.220257"],
        )

    def test_all_is_cached_until_cleared(self):
        self.assertIs(Addons.all(), Addons.all())
        cached = Addons.all()
        Addons.clear_cache()
        self.assertIsNot(Addons.all(), cached)


@mock_multiple_addon_versions
class TestMultipleAddons(TestCase):
    def setUp(self):
        Addons.clear_cache()

    def tearDown(self):
        Addons.clear_cache()

    def test_every_addon_directory_is_loaded(self):
        self.assertEqual(sorted(Addons.all()), ["newtab", "tabtweak"])

    def test_versions_are_keyed_by_directory_name(self):
        self.assertEqual(
            [version.version for version in Addons.by_addon(NEWTAB_ADDON)],
            ["158.0.20260913.220257"],
        )
        self.assertEqual(
            [version.version for version in Addons.by_addon("tabtweak")],
            ["3.1.20260401.120000"],
        )


class TestAddonsDirectoryContents(TestCase):
    def setUp(self):
        Addons.clear_cache()

    def tearDown(self):
        Addons.clear_cache()

    def test_non_directory_entries_are_ignored(self):
        with TemporaryDirectory() as temp_dir:
            versions_path = Path(temp_dir)
            (versions_path / NEWTAB_ADDON).mkdir()
            (versions_path / NEWTAB_ADDON / VERSIONS_FILENAME).write_text(
                json.dumps(
                    [
                        {
                            "version": "158.0.20260913.220257",
                            "shipit_release": "newtab-158.0.0-build1",
                            "xpi_revision": "9779d0c5",
                            "created": "2026-09-13T21:47:36.718463Z",
                        }
                    ]
                )
            )
            (versions_path / "README.md").write_text("not an addon")

            with override_settings(ADDON_VERSIONS_PATH=versions_path):
                self.assertEqual(list(Addons.all()), [NEWTAB_ADDON])


class TestCommittedAddonVersions(TestCase):
    def setUp(self):
        Addons.clear_cache()

    def tearDown(self):
        Addons.clear_cache()

    def test_newtab_versions_are_committed(self):
        self.assertTrue(Addons.by_addon(NEWTAB_ADDON))

    def test_committed_files_match_serialized_form(self):
        for addon, versions in Addons.all().items():
            versions_file = settings.ADDON_VERSIONS_PATH / addon / VERSIONS_FILENAME
            self.assertEqual(
                versions_file.read_text(),
                f"{AddonVersions(root=versions).model_dump_json(indent=2)}\n",
            )

    def test_committed_versions_are_sorted(self):
        for versions in Addons.all().values():
            self.assertEqual(
                versions,
                sorted(versions, key=lambda version: version.sort_key),
            )

    def test_committed_releases_are_unique(self):
        for versions in Addons.all().values():
            self.assertEqual(
                len({version.shipit_release for version in versions}),
                len(versions),
            )


class TestCheckAddonVersions(TestCase):
    def setUp(self):
        Addons.clear_cache()

    def tearDown(self):
        Addons.clear_cache()

    @mock_valid_addon_versions
    def test_valid_addon_versions_do_not_trigger_check_error(self):
        self.assertEqual(check_addon_versions(None), [])

    def test_committed_addon_versions_do_not_trigger_check_error(self):
        self.assertEqual(check_addon_versions(None), [])

    @mock_invalid_addon_versions
    def test_invalid_addon_versions_do_trigger_check_error(self):
        errors = check_addon_versions(None)
        self.assertEqual(len(errors), 1)
        self.assertIn("Error loading Addon Versions", errors[0].msg)

    @mock_missing_addon_versions
    def test_missing_addon_versions_do_trigger_check_error(self):
        errors = check_addon_versions(None)
        self.assertEqual(len(errors), 1)
        self.assertIn("Error loading Addon Versions", errors[0].msg)


class TestAddonVersionsModel(TestCase):
    def test_empty_root_is_valid(self):
        self.assertEqual(AddonVersions.model_validate([]).root, [])
