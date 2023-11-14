from unittest import TestCase

from parameterized import parameterized

from manifesttool.appconfig import AppConfigs
from manifesttool.cli import MANIFESTS_DIR
from manifesttool.repository import Ref
from manifesttool.version import Version, find_versioned_refs, filter_versioned_refs


class VersionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.app_configs = AppConfigs.load_from_directory(MANIFESTS_DIR)

    def test_from_match(self):
        """Tesing Version.from_match."""
        self.assertEqual(Version.from_match({"major": "1"}), Version(1))
        self.assertEqual(Version.from_match({"major": "1", "minor": "2"}), Version(1, 2))
        self.assertEqual(
            Version.from_match({"major": "1", "minor": "2", "patch": "3"}),
            Version(1, 2, 3),
        )

    def test_ordering(self):
        """Testing the comparision functions between two Versions."""
        self.assertEqual(Version(1, 0, 0), Version(1))

        self.assertTrue(Version(1) < Version(1, 1))
        self.assertTrue(Version(1, 1) < Version(1, 1, 1))
        self.assertTrue(Version(1) < Version(2))
        self.assertTrue(
            Version(
                1,
                1,
            )
            < Version(2)
        )
        self.assertTrue(Version(1, 1, 1) < Version(2))

        self.assertFalse(Version(2) < Version(1))
        self.assertFalse(Version(2) < Version(1, 1))
        self.assertFalse(Version(2) < Version(1, 1, 1))
        self.assertFalse(Version(1, 1) < Version(1))
        self.assertFalse(Version(1, 1, 1) < Version(1, 1))

        self.assertTrue(Version(1) <= Version(1))
        self.assertTrue(Version(1) <= Version(1, 1))
        self.assertTrue(Version(1) <= Version(1, 1, 1))
        self.assertTrue(Version(1, 1) <= Version(1, 1))
        self.assertTrue(Version(1, 1) <= Version(1, 1, 1))
        self.assertTrue(Version(1, 1, 1) <= Version(1, 1, 1))

        self.assertFalse(Version(2) <= Version(1))
        self.assertFalse(Version(2) <= Version(1, 1))
        self.assertFalse(Version(2) <= Version(1, 1, 1))
        self.assertFalse(Version(1, 1) <= Version(1))
        self.assertFalse(Version(1, 1, 1) < Version(1, 1))

        self.assertTrue(Version(2) > Version(1))
        self.assertTrue(Version(2) > Version(1, 1))
        self.assertTrue(Version(2) > Version(1, 1, 1))
        self.assertTrue(Version(1, 1) > Version(1))
        self.assertTrue(Version(1, 1, 1) > Version(1, 1))

        self.assertFalse(Version(1) > Version(2))
        self.assertFalse(Version(1) > Version(1, 1))
        self.assertFalse(Version(1, 1) > Version(1, 1, 1))
        self.assertFalse(Version(1, 1) > Version(2))
        self.assertFalse(Version(1, 1, 1) > Version(2))

        self.assertTrue(Version(1) >= Version(1))
        self.assertTrue(Version(1, 1) >= Version(1))
        self.assertTrue(Version(1, 1) >= Version(1, 1))
        self.assertTrue(Version(1, 1, 1) >= Version(1, 1, 1))

        self.assertFalse(Version(1) >= Version(2))
        self.assertFalse(Version(1) >= Version(1, 1))
        self.assertFalse(Version(1, 1) >= Version(2))
        self.assertFalse(Version(1, 1) >= Version(1, 1, 1))
        self.assertFalse(Version(1, 1, 1) >= Version(2))

    @parameterized.expand(
        [
            (
                "fenix",
                [
                    "main",
                    "releases_v109",
                    "releases_v110",
                ],
                {
                    Version(109): Ref("releases_v109"),
                    Version(110): Ref("releases_v110"),
                },
            ),
            (
                "firefox_ios",
                [
                    "main",
                    "116.3",
                    "release/v116.2",
                    "release/v117",
                    "v11.x",
                    "v105.0",
                    "v32.AS2",
                ],
                {
                    Version(116, 2): Ref("release/v116.2"),
                    Version(117): Ref("release/v117"),
                },
            ),
            (
                "focus_android",
                [
                    "main",
                    "releases_v109",
                    "releases_v110",
                ],
                {
                    Version(109): Ref("releases_v109"),
                    Version(110): Ref("releases_v110"),
                },
            ),
            (
                "focus_ios",
                [
                    "main",
                    "3.10.1",
                    "34",
                    "39.0",
                    "release_v98.1",
                    "releases/v8.1.6",
                    "releases_v107.1",
                    "releases_v120",
                    "releases_v999",
                ],
                {
                    Version(107, 1): Ref("releases_v107.1"),
                    Version(120): Ref("releases_v120"),
                    Version(999): Ref("releases_v999"),
                },
            ),
        ]
    )
    def test_find_versioned_branches(
        self,
        app_name: str,
        names: list[str],
        expected: dict[Version, Ref],
    ):
        """Testing find_versioned_refs with real branch data."""
        self._test_find_versioned_refs(
            self.app_configs.__root__[app_name].branch_re,
            [Ref(name) for name in names],
            expected,
        )

    @parameterized.expand(
        [
            (
                "fenix",
                [
                    "components-v118.0",
                    "components-v118.2",
                    "components-v119.1.1",
                    "components-v120.0b9",
                    "fenix-v118.0",
                    "fenix-v118.2",
                    "fenix-v119.1.1",
                    "fenix-v120.0b9",
                    "focus-v118.0",
                    "focus-v118.2",
                    "focus-v119.1.1",
                    "focus-v120.0b9",
                    "klar-v119.1.1",
                    "klar-v118.2",
                    "v109.0b2",
                    "v108.1.1",
                ],
                {
                    Version(118): Ref("fenix-v118.0"),
                    Version(118, 2): Ref("fenix-v118.2"),
                    Version(119, 1, 1): Ref("fenix-v119.1.1"),
                },
            ),
            (
                "firefox_ios",
                [
                    "v119.2",
                    "v119.0",
                    "v104",
                    "v16.2-b",
                    "v3.0b8",
                    "FirefoxNightly-v6.0b2",
                    "FirefoxBeta-v6.0b8",
                    "Firefox-v6.1b1",
                    "AuroraV30",
                    "105.0",
                    "20.1-rel",
                    "1.0.0RC3",
                ],
                {
                    Version(119, 2): Ref("v119.2"),
                    Version(119): Ref("v119.0"),
                },
            ),
            (
                "focus_android",
                [
                    "components-v118.0",
                    "components-v118.2",
                    "components-v119.1.1",
                    "components-v120.0b9",
                    "fenix-v118.0",
                    "fenix-v118.2",
                    "fenix-v119.1.1",
                    "fenix-v120.0b9",
                    "focus-v118.0",
                    "focus-v118.2",
                    "focus-v119.1.1",
                    "focus-v120.0b9",
                    "klar-v119.1.1",
                    "klar-v118.2",
                    "v109.0b2",
                    "v108.1.1",
                ],
                {
                    Version(118): Ref("focus-v118.0"),
                    Version(118, 2): Ref("focus-v118.2"),
                    Version(119, 1, 1): Ref("focus-v119.1.1"),
                },
            ),
            (
                "focus_ios",
                [
                    "v999.0.0",
                    "v120.0",
                    "v98.1.0",
                    "v97.0.0-rc.1",
                    "8.1.6",
                ],
                {
                    Version(999): Ref("v999.0.0"),
                    Version(120): Ref("v120.0"),
                    Version(98, 1): Ref("v98.1.0"),
                },
            ),
        ]
    )
    def test_find_versioned_tags(
        self,
        app_name: str,
        names: list[str],
        expected: dict[Version, Ref],
    ):
        """Testing find_versioned_refs with real tag data."""
        self._test_find_versioned_refs(
            self.app_configs.__root__[app_name].tag_re,
            [Ref(name) for name in names],
            expected,
        )

    def _test_find_versioned_refs(
        self,
        pattern: str,
        refs: list[Ref],
        expected: dict[Version, Ref],
    ):
        versions = find_versioned_refs(refs, pattern)

        self.assertEqual(
            versions,
            expected,
        )

    def test_filter_versioned_refs(self):
        """Testing filter_versioned_refs."""
        versioned_refs = {
            Version(major, minor, patch): Ref(f"v{major}.{minor}.{patch}")
            for major in (99, 100, 101, 102, 103, 104, 105)
            for minor in (0, 1)
            for patch in (0, 1)
        }

        versioned_refs[Version(9999)] = Ref("over_9000")

        result = filter_versioned_refs(versioned_refs, Version(100), ["over_9000"])

        self.assertEqual(
            set(result.keys()),
            {
                Version(105),
                Version(105, 1),
                Version(105, 1, 1),
                Version(105, 0, 1),
                Version(104),
                Version(104, 1),
                Version(104, 1, 1),
                Version(104, 0, 1),
                Version(103),
                Version(103, 1),
                Version(103, 1, 1),
                Version(103, 0, 1),
                Version(102),
                Version(102, 1),
                Version(102, 1, 1),
                Version(102, 0, 1),
                Version(101),
                Version(101, 1),
                Version(101, 1, 1),
                Version(101, 0, 1),
                Version(100),
                Version(100, 1),
                Version(100, 1, 1),
                Version(100, 0, 1),
            },
        )

    def test_filter_versioned_refs_focus_ios(self):
        """Testing filter_versioned_refs for focus-ios with real data."""
        app_config = self.app_configs.__root__["focus_ios"]
        versioned_tags = {
            Version(999): Ref("v999.0.0"),
            Version(120): Ref("v120.0"),
            Version(98, 1): Ref("v98.1.0"),
        }
        filtered_tags = filter_versioned_refs(
            versioned_tags, Version(100), app_config.ignored_tags
        )
        self.assertEqual(
            set(filtered_tags.keys()),
            {Version(120)},
        )

        versioned_branches = {
            Version(107, 1): Ref("releases_v107.1"),
            Version(120): Ref("releases_v120"),
            Version(999): Ref("releases_v999"),
        }
        filtered_branches = filter_versioned_refs(
            versioned_branches,
            Version(100),
            app_config.ignored_branches,
        )
        self.assertEqual(
            set(filtered_branches.keys()),
            {Version(107, 1), Version(120)},
        )
