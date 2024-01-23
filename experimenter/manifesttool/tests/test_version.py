from typing import Any, Optional
from unittest import TestCase

import responses
from parameterized import parameterized
from responses import matchers
from pydantic import BaseModel, ValidationError

from manifesttool.appconfig import (
    AppConfig,
    AppConfigs,
    DiscoveryStrategy,
    DiscoveryStrategyType,
    ReleaseDiscovery,
    Repository,
    RepositoryType,
    VersionFile,
)
from manifesttool.cli import MANIFEST_DIR
from manifesttool.github_api import GITHUB_API_URL
from manifesttool.hgmo_api import HGMO_URL
from manifesttool.repository import Ref
from manifesttool.tests.test_github_api import make_responses_for_fetch
from manifesttool.version import (
    Version,
    filter_versioned_refs,
    find_versioned_refs,
    parse_version_file,
    resolve_ref_versions,
)


class VersionModel(BaseModel):
    version: Version


class VersionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.app_configs = AppConfigs.load_from_directory(MANIFEST_DIR)

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
                ],
                {
                    Version(107, 1): Ref("releases_v107.1"),
                    Version(120): Ref("releases_v120"),
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
        strategy = next(
            release_discovery.__root__
            for release_discovery in self.app_configs.__root__[
                app_name
            ].release_discovery.strategies
            if release_discovery.__root__.type == DiscoveryStrategyType.TAGGED
        )
        self._test_find_versioned_refs(
            strategy.branch_re,
            [Ref(name) for name in names],
            strategy.ignored_branches,
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
        strategy = next(
            release_discovery.__root__
            for release_discovery in self.app_configs.__root__[
                app_name
            ].release_discovery.strategies
            if release_discovery.__root__.type == DiscoveryStrategyType.TAGGED
        )
        self._test_find_versioned_refs(
            strategy.tag_re,
            [Ref(name) for name in names],
            strategy.ignored_tags,
            expected,
        )

    def _test_find_versioned_refs(
        self,
        pattern: str,
        refs: list[Ref],
        ignored_refs: Optional[list[str]],
        expected: dict[Version, Ref],
    ):
        versions = find_versioned_refs(refs, pattern, ignored_refs)

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

        result = filter_versioned_refs(versioned_refs, Version(100))

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

    @parameterized.expand(
        [
            ("bogus", None),
            ("1", Version(1)),
            ("1\n", Version(1)),
            ("1a1", Version(1)),
            ("1.2", Version(1, 2)),
            ("1.2\n", Version(1, 2)),
            ("1.2a1", Version(1, 2)),
            ("1.2.1", Version(1, 2, 1)),
            ("1.2.1\n", Version(1, 2, 1)),
            ("1.2.1a1", Version(1, 2, 1)),
        ]
    )
    def test_version_parse_validate(self, s: str, expected: Optional[Version]):
        """Testing Version.parse and Version.validate"""
        self.assertEqual(Version.parse(s), expected)

        obj = {"version": s}

        if expected:
            model = VersionModel.parse_obj(obj)
            self.assertEqual(model.version, expected)
        else:
            with self.assertRaisesRegexp(ValidationError, f"Invalid version {repr(s)}"):
                VersionModel.parse_obj(obj)

    @parameterized.expand(
        [
            1,
            True,
            None,
        ]
    )
    def test_validate_invalid_types(self, v: Any):
        """Testing Version.validate with invalid input types."""
        with self.assertRaises(ValidationError):
            VersionModel.parse_obj({"version": v})

    def test_validate_version(self):
        """Testing Version.validate allows Version instances."""
        model = VersionModel(version=Version(1, 2, 3))
        self.assertEqual(model.version, Version(1, 2, 3))

    @parameterized.expand(
        [
            ("121.0a1\n", Version(121)),
            ("119.0.1\n", Version(119, 0, 1)),
            ("bogus", None),
        ],
    )
    def test_parse_version_file_plain_text(self, contents, expected):
        """Testing parse_version_file with a plain-text version file."""
        version_file = VersionFile.create_plain_text("version.txt")
        self.assertEqual(parse_version_file(version_file, contents), expected)

    @parameterized.expand(
        [
            ("121.0", Version(121)),
            ("121.1", Version(121, 1)),
            ("bogus", None),
        ]
    )
    def test_parse_version_file_plist(self, version_str, expected):
        """Testing parse_version_file with a plist version file."""
        version_file = VersionFile.create_plist("info.plist", "Version")
        contents = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'
            ' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n'
            "<dict>\n"
            "  <key>Version</key>\n"
            f"  <string>{version_str}</string>\n"
            "</dict>\n"
            "</plist>\n"
        )

        self.assertEqual(parse_version_file(version_file, contents), expected)

    @parameterized.expand(
        [
            (
                app_config,
                [
                    (Ref("v120", "r0"), b"120.0a1\n"),
                    (Ref("v120.1", "r1"), b"120.1a1\n"),
                    (Ref("v121", "r2"), b"121.0a1\n"),
                ],
                {
                    Version(120): Ref("v120", "r0"),
                    Version(120, 1): Ref("v120.1", "r1"),
                    Version(121): Ref("v121", "r2"),
                },
            )
            for app_config in (
                AppConfig(
                    slug="fml-app",
                    repo=Repository(
                        type=RepositoryType.GITHUB,
                        name="fml-app",
                    ),
                    fml_path="nimbus.fml.yaml",
                    release_discovery=ReleaseDiscovery(
                        version_file=VersionFile.create_plain_text("version.txt"),
                        strategies=[DiscoveryStrategy.create_tagged(branch_re="")],
                    ),
                ),
                AppConfig(
                    slug="legacy-app",
                    repo=Repository(
                        type=RepositoryType.HGMO,
                        name="legacy-app",
                        default_branch="tip",
                    ),
                    experimenter_yaml_path="nimbus.yaml",
                    release_discovery=ReleaseDiscovery(
                        version_file=VersionFile.create_plain_text("version.txt"),
                        strategies=[DiscoveryStrategy.create_tagged(branch_re="")],
                    ),
                ),
            )
        ]
    )
    @responses.activate
    def test_resolve_ref_versions(
        self,
        app_config: AppConfig,
        bodies: list[tuple[Ref, str]],
        expected: dict[Version, Ref],
    ):
        """Testing resolve_ref_versions."""
        refs = []
        rsps = []
        for ref, body in bodies:
            refs.append(ref)

            if app_config.repo.type == RepositoryType.GITHUB:
                rsps.extend(
                    make_responses_for_fetch(
                        app_config.repo.name,
                        ref.target,
                        app_config.release_discovery.version_file.__root__.path,
                        body,
                    )
                )
            else:
                rsps.append(
                    responses.get(
                        f"{HGMO_URL}/{app_config.repo.name}/raw-file/"
                        f"{ref.target}/{app_config.release_discovery.version_file.__root__.path}",
                        body=body,
                    )
                )

        result = resolve_ref_versions(app_config, refs)

        for rsp in rsps:
            self.assertEqual(rsp.call_count, 1)

        self.assertEqual(result, expected)

    @parameterized.expand(
        [
            (
                app_config,
                [
                    (Ref("v120", "r0"), "a/version.txt", b"120.0a1\n"),
                    (Ref("v120.1", "r1"), "a/version.txt", b"120.1a1\n"),
                    (Ref("v121", "r2"), "b/version.txt", b"121.0a1\n"),
                ],
                {
                    Version(120): Ref("v120", "r0"),
                    Version(120, 1): Ref("v120.1", "r1"),
                    Version(121): Ref("v121", "r2"),
                },
            )
            for app_config in (
                AppConfig(
                    slug="fml-app",
                    repo=Repository(
                        type=RepositoryType.GITHUB,
                        name="fml-app",
                    ),
                    fml_path="nimbus.fml.yaml",
                    release_discovery=ReleaseDiscovery(
                        version_file=VersionFile.create_plain_text(
                            ["a/version.txt", "b/version.txt"]
                        ),
                        strategies=[DiscoveryStrategy.create_tagged(branch_re="")],
                    ),
                ),
                AppConfig(
                    slug="legacy-app",
                    repo=Repository(
                        type=RepositoryType.HGMO,
                        name="legacy-app",
                        default_branch="default",
                    ),
                    fml_path="experimenter.yaml",
                    release_discovery=ReleaseDiscovery(
                        version_file=VersionFile.create_plain_text(
                            ["a/version.txt", "b/version.txt"]
                        ),
                        strategies=[DiscoveryStrategy.create_tagged(branch_re="")],
                    ),
                ),
            )
        ]
    )
    @responses.activate
    def test_resolve_ref_versions_multiple_files(self, app_config, bodies, expected):
        version_paths = app_config.release_discovery.version_file.__root__.path

        refs = []
        rsps = []
        for ref, good_path, body in bodies:
            refs.append(ref)

            bad_path = next(p for p in version_paths if p != good_path)

            if app_config.repo.type == RepositoryType.GITHUB:
                rsps.extend(
                    make_responses_for_fetch(
                        app_config.repo.name,
                        ref.target,
                        good_path,
                        body,
                    )
                )
                responses.get(
                    f"{GITHUB_API_URL}/repos/{app_config.repo.name}/contents/{bad_path}",
                    match=[matchers.query_param_matcher({"ref": ref.target})],
                    status=404,
                    body=b"",
                )
            else:
                url_template = (
                    f"{HGMO_URL}/{app_config.repo.name}/raw-file/"
                    f"{ref.target}/{{path}}"
                )
                rsps.append(responses.get(url_template.format(path=good_path), body=body))
                responses.get(url_template.format(path=bad_path), status=404, body=b"")

        result = resolve_ref_versions(app_config, refs)

        for rsp in rsps:
            self.assertEqual(rsp.call_count, 1)

        self.assertEqual(result, expected)

    @responses.activate
    def test_resolve_ref_cannot_find_version(self):
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-app",
            ),
            fml_path="nimbus.fml.yaml",
            release_discovery=ReleaseDiscovery(
                version_file=VersionFile.create_plain_text(
                    ["a/version.txt", "b/version.txt"]
                ),
                strategies=[DiscoveryStrategy.create_tagged(branch_re="")],
            ),
        )

        rsps = [
            responses.get(
                f"{GITHUB_API_URL}/repos/{app_config.repo.name}/contents/{path}",
                match=[matchers.query_param_matcher({"ref": "foo"})],
                status=404,
                body=b"",
            )
            for path in app_config.release_discovery.version_file.__root__.path
        ]

        with self.assertRaisesRegex(
            Exception, "Could not find version file for app fml-app"
        ):
            resolve_ref_versions(app_config, [Ref("main", "foo")])

        for rsp in rsps:
            self.assertEqual(rsp.call_count, 1)
