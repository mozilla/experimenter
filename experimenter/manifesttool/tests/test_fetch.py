import json
from contextlib import redirect_stderr, contextmanager
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterable, Optional
from unittest import TestCase
from unittest.mock import call, patch

import responses
import yaml
from parameterized import parameterized

import manifesttool
from manifesttool import fetch
from manifesttool.appconfig import (
    AppConfig,
    Repository,
    RepositoryType,
    VersionFile,
    VersionFileType,
)
from manifesttool.fetch import (
    FetchResult,
    fetch_fml_app,
    fetch_legacy_app,
    fetch_releases,
)
from manifesttool.nimbus_cli import _get_experimenter_yaml_path, _get_fml_path
from manifesttool.repository import Ref
from manifesttool.version import Version

FML_APP_CONFIG = AppConfig(
    slug="fml-app",
    repo=Repository(
        type=RepositoryType.GITHUB,
        name="fml-repo",
    ),
    fml_path="nimbus.fml.yaml",
)

LEGACY_APP_CONFIG = AppConfig(
    slug="legacy-app",
    repo=Repository(
        type=RepositoryType.HGMO,
        name="legacy-repo",
    ),
    experimenter_yaml_path="experimenter.yaml",
)

FEATURE_JSON_SCHEMA_PATH = "feature.schema.json"

LEGACY_MANIFEST_PATH = "experimenter.yaml"

LEGACY_MANIFEST = {
    "feature": {
        "description": "Feature",
        "hasExposure": False,
        "variables": {},
        "schema": {
            "path": FEATURE_JSON_SCHEMA_PATH,
            "uri": "resource://schema.json",
        },
    },
}

FEATURE_JSON_SCHEMA = {"type": "object", "additionalProperties": False}


def generate_fml(app_config: AppConfig, channel: str) -> dict[str, Any]:
    """Generate a FML manifest for the given app and channel."""
    return {
        "version": "1.0.0",
        "about": {
            "description": f"Generated manifest for {app_config.slug} {channel}",
        },
        "channels": [channel],
        "features": {
            "generated": {
                "description": "Generated feature",
                "variables": {
                    "enabled": {
                        "description": "Is this feature enabled?",
                        "type": "Boolean",
                        "default": False,
                    },
                },
            },
        },
    }


def mock_download_single_file(
    manifest_dir: Path,
    app_config: AppConfig,
    channel: str,
    ref: str,
    version: Optional[Version],
):
    """A mock version of `nimbus fml -- single file`."""
    filename = _get_fml_path(manifest_dir, app_config, channel, version)
    with filename.open("w") as f:
        yaml.dump(generate_fml(app_config, channel), f)


def make_mock_fetch_file(paths=None):
    if paths is None:
        paths = {
            LEGACY_MANIFEST_PATH: LEGACY_MANIFEST,
            FEATURE_JSON_SCHEMA_PATH: FEATURE_JSON_SCHEMA,
        }

    def mock_fetch_file(
        repo: str,
        file_path: str,
        rev: str,
        download_path: Path,
    ):
        """A mock version of hgmo_api.fetch_file."""

        try:
            content = paths[file_path]
        except KeyError as e:
            raise Exception(
                f"Unexpected file path ({file_path}) passed to hgmo_api.fetch_file"
            ) from e

        with download_path.open("w", newline="\n") as f:
            json.dump(content, f)

    return mock_fetch_file


def mock_fetch(
    manifest_dir: Path,
    app_name: str,
    app_config: AppConfig,
    ref: Optional[Ref],
    version: Optional[Version] = None,
) -> FetchResult:
    """A mock version of fetch_fml_app and fetch_legacy_app that returns success."""
    return FetchResult(app_name, ref, version)


@contextmanager
def mocks_for_fetch_releases(
    app_config: AppConfig,
    branches: list[Ref],
    tags: Optional[list[Ref]],
    ref_versions: dict[str, Version],
):
    """Create a set of mocks to call fetch_releases.

    Args:
        app_config:
            The app configuration.

            The ``version_file`` and ``branch_re`` fields are required.

        branches:
            The list of refs to return from ``get_branches()``.

        Tags:
            The list of refs to return from ``get_tags()``.

            If ``None``, ``app_config.tag_re`` must also be ``None``.

        ref_versions:
            A mapping of resolved refs to Versions.

            This argument is used to generate a mock for ``fetch_file()``.

    Yields:
        A 3-tuple of the mocks for ``get_branches``, ``get_tags``, and ``fetch_file``.
    """
    assert app_config.repo.type == RepositoryType.GITHUB
    assert app_config.branch_re is not None

    # Mocking plist files is more annoying.
    assert app_config.version_file is not None
    assert app_config.version_file.__root__.type == VersionFileType.PLAIN_TEXT

    # Ensure tags are defined if app specifies a tag regex.
    assert app_config.tag_re is None or tags is not None

    def mock_get_branches(*args):
        return branches

    def mock_get_tags(*args):
        assert tags is not None
        return tags

    def mock_fetch_file(
        repo: str, path: str, ref: str, download_path: Optional[Path] = None
    ):
        assert repo == app_config.repo.name
        assert download_path is None
        assert path == app_config.version_file.__root__.path
        assert ref in ref_versions

        return str(ref_versions[ref])

    with (
        patch.object(
            manifesttool.github_api, "get_branches", side_effect=mock_get_branches
        ) as get_branches,
        patch.object(
            manifesttool.github_api, "get_tags", side_effect=mock_get_tags
        ) as get_tags,
        patch.object(
            manifesttool.github_api, "fetch_file", side_effect=mock_fetch_file
        ) as fetch_file,
    ):
        yield (
            get_branches,
            get_tags,
            fetch_file,
        )


class FetchTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Use responses to ensure we don't make any HTTP calls.
        responses.start()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        responses.stop()

    @patch.object(
        fetch.github_api, "get_main_ref", side_effect=lambda *args: Ref("main", "ref")
    )
    @patch.object(
        fetch.nimbus_cli, "download_single_file", side_effect=mock_download_single_file
    )
    @patch.object(
        fetch.nimbus_cli, "get_channels", side_effect=lambda *args: ["release", "beta"]
    )
    def test_fetch_fml(self, get_channels, download_single_file, get_main_ref):
        """Testing fetch_fml_app."""
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("fml-app").mkdir()

            result = fetch_fml_app(manifest_dir, "app", FML_APP_CONFIG)
            self.assertIsNone(result.exc)

            get_main_ref.assert_called_with(FML_APP_CONFIG.repo.name)
            get_channels.asset_called_with(FML_APP_CONFIG, "ref")
            download_single_file.assert_has_calls(
                [
                    call(manifest_dir, FML_APP_CONFIG, "release", "ref", None),
                    call(manifest_dir, FML_APP_CONFIG, "beta", "ref", None),
                ]
            )

            experimenter_manifest_path = _get_experimenter_yaml_path(
                manifest_dir,
                FML_APP_CONFIG,
                None,
            )
            self.assertTrue(
                experimenter_manifest_path.exists(), "experimenter.yaml should exist"
            )

            with experimenter_manifest_path.open() as f:
                experimenter_manifest = yaml.safe_load(f)

            self.assertEqual(
                experimenter_manifest,
                {
                    "generated": {
                        "description": "Generated feature",
                        "hasExposure": True,
                        "exposureDescription": "",
                        "variables": {
                            "enabled": {
                                "description": "Is this feature enabled?",
                                "type": "boolean",
                            },
                        },
                    },
                },
            )

    @patch.object(fetch.github_api, "get_main_ref")
    @patch.object(fetch.nimbus_cli, "get_channels", side_effect=lambda *args: ["release"])
    @patch.object(fetch.nimbus_cli, "download_single_file")
    @patch.object(fetch.nimbus_cli, "generate_experimenter_yaml")
    def test_fetch_fml_ref(
        self, generate_experimenter_yaml, download_single_file, get_channels, get_main_ref
    ):
        """Testing fetch_fml_app with a specific ref."""
        ref = Ref("custom", "resolved")
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("fml-app").mkdir()

            result = fetch_fml_app(manifest_dir, "app", FML_APP_CONFIG, ref)
            self.assertIsNone(result.exc)

            get_main_ref.assert_not_called()
            get_channels.assert_called_with(FML_APP_CONFIG, ref.resolved)
            download_single_file.assert_called_with(
                manifest_dir,
                FML_APP_CONFIG,
                "release",
                ref.resolved,
                None,
            )
            generate_experimenter_yaml.assert_called_with(
                manifest_dir,
                FML_APP_CONFIG,
                "release",
                None,
            )

    def test_fetch_fml_version_no_ref(self):
        """Testing fetch_fml_app with a version but no ref results in an error."""
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("fml-app").mkdir()

            with self.assertRaisesRegex(
                ValueError, "Cannot fetch specific version without a ref."
            ):
                fetch_fml_app(manifest_dir, "app", FML_APP_CONFIG, version=Version(1))

    @patch.object(fetch.github_api, "get_main_ref")
    @patch.object(
        fetch.nimbus_cli, "get_channels", side_effect=lambda *args: ["release", "beta"]
    )
    @patch.object(
        fetch.nimbus_cli, "download_single_file", side_effect=mock_download_single_file
    )
    @patch.object(
        fetch.nimbus_cli,
        "generate_experimenter_yaml",
        wraps=fetch.nimbus_cli.generate_experimenter_yaml,
    )
    def test_fetch_fml_ref_version(
        self, generate_experimenter_yaml, download_single_file, get_channels, get_main_ref
    ):
        """Testing fetch_fml_app with a ref and a version."""
        ref = Ref("v123", "foo")
        version = Version(1, 2, 3)
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("fml-app").mkdir()

            result = fetch_fml_app(manifest_dir, "app", FML_APP_CONFIG, ref, version)
            self.assertEqual(result, FetchResult("app", ref, version))

            get_main_ref.assert_not_called()
            get_channels.assert_called_with(FML_APP_CONFIG, ref.resolved)
            download_single_file.assert_has_calls(
                [
                    call(manifest_dir, FML_APP_CONFIG, "release", ref.resolved, version),
                    call(manifest_dir, FML_APP_CONFIG, "beta", ref.resolved, version),
                ]
            )

            generate_experimenter_yaml.assert_called_once_with(
                manifest_dir, FML_APP_CONFIG, "release", version
            )

            experimenter_manifest_path = _get_experimenter_yaml_path(
                manifest_dir, FML_APP_CONFIG, version
            )

            self.assertIn("v1.2.3", str(experimenter_manifest_path))
            self.assertTrue(experimenter_manifest_path.exists())

    @patch.object(
        fetch.github_api, "get_main_ref", side_effect=Exception("Connection error")
    )
    def test_fetch_fml_exception(self, get_main_ref):
        """Testing fetch_fml_app when an exception is caught."""
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)

            result = fetch_fml_app(manifest_dir, "fml-app", FML_APP_CONFIG)
            self.assertIsNotNone(result.exc)
            self.assertEqual(str(result.exc), "Connection error")

    def test_fetch_fml_hgmo(self):
        """Testing fetch_fml_app with an hg.mozilla.org repository fails."""
        app_config = AppConfig(
            slug="invalid",
            repo=Repository(
                type=RepositoryType.HGMO,
                name="invalid",
            ),
            fml_path="nimbus.fml.yaml",
        )

        with self.assertRaisesRegex(
            Exception,
            "FML-based apps on hg.mozilla.org are not supported.",
        ):
            fetch_fml_app(Path("."), "invalid", app_config)

    def test_fetch_fml_unresolved_ref(self):
        """Testing fetch_fml_app with an unresolved ref."""
        with self.assertRaisesRegex(
            ValueError,
            "fetch_fml_app: ref `foo` is not resolved",
        ):
            fetch_fml_app(Path("."), "repo", FML_APP_CONFIG, Ref("foo"))

    @patch.object(fetch.nimbus_cli, "download_single_file")
    @patch.object(fetch.nimbus_cli, "generate_experimenter_yaml")
    @patch.object(fetch.nimbus_cli, "get_channels", lambda *args: [])
    def test_fetch_fml_no_channels(
        self, generate_experimenter_yaml, download_single_file
    ):
        """Testing fetch_fml_app when nimbus-cli reports no channels."""
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)

            result = fetch_fml_app(
                manifest_dir, "app", FML_APP_CONFIG, ref=Ref("main", "0" * 40)
            )
            self.assertIs(type(result.exc), Exception)
            self.assertEqual(str(result.exc), "No channels found")

            self.assertFalse(
                manifest_dir.joinpath(FML_APP_CONFIG.slug, "experimenter.yaml").exists(),
                "experimenter.yaml should not be created",
            )

        download_single_file.assert_not_called()
        generate_experimenter_yaml.assert_not_called()

    @patch.object(fetch.hgmo_api, "get_tip_rev", lambda *args: Ref("tip", "ref"))
    @patch.object(fetch.hgmo_api, "fetch_file", side_effect=make_mock_fetch_file())
    def test_fetch_legacy(self, fetch_file):
        """Testing fetch_legacy_app."""
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("legacy-app").mkdir()

            result = fetch_legacy_app(manifest_dir, "app", LEGACY_APP_CONFIG)
            self.assertIsNone(result.exc)

            fetch_file.assert_has_calls(
                [
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        LEGACY_MANIFEST_PATH,
                        "ref",
                        manifest_dir / LEGACY_APP_CONFIG.slug / "experimenter.yaml",
                    ),
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        FEATURE_JSON_SCHEMA_PATH,
                        "ref",
                        manifest_dir
                        / LEGACY_APP_CONFIG.slug
                        / "schemas"
                        / FEATURE_JSON_SCHEMA_PATH,
                    ),
                ]
            )
            self.assertEqual(fetch_file.call_count, 2)

    @patch.object(fetch.hgmo_api, "get_tip_rev")
    @patch.object(fetch.hgmo_api, "fetch_file", side_effect=make_mock_fetch_file())
    def test_fetch_legacy_ref(self, fetch_file, get_tip_rev):
        """Testing fetch_legacy_app with a specific ref."""
        ref = Ref("custom", "resolved")
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("legacy-app").mkdir()

            result = fetch_legacy_app(manifest_dir, "app", LEGACY_APP_CONFIG, ref)
            self.assertIsNone(result.exc)

            get_tip_rev.assert_not_called()
            fetch_file.assert_has_calls(
                [
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        LEGACY_MANIFEST_PATH,
                        ref.resolved,
                        manifest_dir / LEGACY_APP_CONFIG.slug / "experimenter.yaml",
                    ),
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        FEATURE_JSON_SCHEMA_PATH,
                        ref.resolved,
                        manifest_dir
                        / LEGACY_APP_CONFIG.slug
                        / "schemas"
                        / FEATURE_JSON_SCHEMA_PATH,
                    ),
                ],
            )

    def test_fetch_legacy_version_no_ref(self):
        """Testing fetch_legacy_app with a version but no ref results in an error."""
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("legacy-app").mkdir()

            with self.assertRaisesRegex(
                ValueError, "Cannot fetch specific version without a ref."
            ):
                fetch_legacy_app(
                    manifest_dir, "app", LEGACY_APP_CONFIG, version=Version(1)
                )

    @patch.object(fetch.hgmo_api, "get_tip_rev")
    @patch.object(fetch.hgmo_api, "fetch_file", side_effect=make_mock_fetch_file())
    def test_fetch_legacy_ref_version(self, fetch_file, get_tip_rev):
        """Testing fetch_legacy_app with a ref and a version."""
        ref = Ref("v1.2.3", "foo")
        version = Version(1, 2, 3)

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("legacy-app").mkdir()

            result = fetch_legacy_app(
                manifest_dir, "app", LEGACY_APP_CONFIG, ref, version
            )
            self.assertEqual(result, FetchResult("app", ref, version))

            get_tip_rev.assert_not_called()
            fetch_file.assert_has_calls(
                [
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        LEGACY_MANIFEST_PATH,
                        ref.resolved,
                        manifest_dir
                        / LEGACY_APP_CONFIG.slug
                        / f"v{version}"
                        / "experimenter.yaml",
                    ),
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        FEATURE_JSON_SCHEMA_PATH,
                        ref.resolved,
                        manifest_dir
                        / LEGACY_APP_CONFIG.slug
                        / f"v{version}"
                        / "schemas"
                        / FEATURE_JSON_SCHEMA_PATH,
                    ),
                ]
            )

    @patch.object(fetch.hgmo_api, "get_tip_rev", lambda *args: Ref("tip", "ref"))
    @patch.object(
        fetch.hgmo_api,
        "fetch_file",
        side_effect=make_mock_fetch_file(
            {
                LEGACY_MANIFEST_PATH: {
                    "feature": LEGACY_MANIFEST["feature"],
                    "feature-2": LEGACY_MANIFEST["feature"],
                },
                FEATURE_JSON_SCHEMA_PATH: FEATURE_JSON_SCHEMA,
            }
        ),
    )
    def test_fetch_legacy_repeated_schema(self, fetch_file):
        """Testing fetch_legacy_app does not fetch the same schema twice."""
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("legacy-app").mkdir()

            result = fetch_legacy_app(manifest_dir, "app", LEGACY_APP_CONFIG)
            self.assertIsNone(result.exc)

            fetch_file.assert_has_calls(
                [
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        LEGACY_MANIFEST_PATH,
                        "ref",
                        manifest_dir / LEGACY_APP_CONFIG.slug / "experimenter.yaml",
                    ),
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        FEATURE_JSON_SCHEMA_PATH,
                        "ref",
                        manifest_dir
                        / LEGACY_APP_CONFIG.slug
                        / "schemas"
                        / FEATURE_JSON_SCHEMA_PATH,
                    ),
                ]
            )
            self.assertEqual(fetch_file.call_count, 2)

    @patch.object(
        fetch.hgmo_api, "get_tip_rev", side_effect=Exception("Connection error")
    )
    def test_fetch_legacy_exception(self, get_tip_rev):
        """Testing fetch_fml_app when an exception is caught."""
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)

            result = fetch_legacy_app(manifest_dir, "legacy_app", LEGACY_APP_CONFIG)
            self.assertIsNotNone(result.exc)
            self.assertEqual(str(result.exc), "Connection error")

    def test_fetch_legacy_github(self):
        """Testing fetch_legacy_app with a GitHub repository fails."""
        app_config = AppConfig(
            slug="invalid",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="invalid",
            ),
            experimenter_yaml_path="experimenter.yaml",
        )

        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                Exception,
                "Legacy experimenter.yaml apps on GitHub are not supported.",
            ):
                fetch_legacy_app(Path(tmp), "invalid", app_config)

    def test_fetch_legacy_unresolved_ref(self):
        """Testing fetch_legacy_app with an unresolved ref."""
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("legacy-app").mkdir()

            with self.assertRaisesRegex(
                ValueError,
                "fetch_legacy_app: ref foo is not resolved",
            ):
                fetch_legacy_app(manifest_dir, "repo", LEGACY_APP_CONFIG, Ref("foo"))

    @parameterized.expand(
        [
            (
                AppConfig(
                    slug="legacy-app",
                    repo=Repository(
                        type=RepositoryType.HGMO,
                        name="legacy-repo",
                    ),
                    experimenter_yaml_path="experimenter.yaml",
                ),
                "Cannot fetch releases for apps hosted on hg.mozilla.org",
            ),
            (
                AppConfig(
                    slug="legacy-app",
                    repo=Repository(
                        type=RepositoryType.GITHUB,
                        name="legacy-repo",
                    ),
                    experimenter_yaml_path="experimenter.yaml",
                ),
                "Cannot fetch releases for legacy apps",
            ),
            (
                AppConfig(
                    slug="fml-app",
                    repo=Repository(
                        type=RepositoryType.GITHUB,
                        name="fml-repo",
                    ),
                    fml_path="nimbus.fml.yaml",
                ),
                "App app does not have a version file.",
            ),
        ]
    )
    def test_fetch_releases_unsupported_apps(
        self, app_config: AppConfig, exc_message: str
    ):
        """Testing fetch_releases with unsupported apps."""
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath(app_config.slug).mkdir()

            with self.assertRaisesRegex(Exception, exc_message):
                fetch_releases(manifest_dir, "app", app_config)

    @patch.object(fetch.github_api, "get_branches")
    def test_fetch_releases_no_branch_re(self, app_config):
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path="nimbus.fml.yaml",
            version_file=VersionFile.create_plain_text("version.txt"),
        )
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath(app_config.slug).mkdir()

            f = StringIO()
            with redirect_stderr(f):
                fetch_releases(manifest_dir, "app", app_config)

            self.assertIn("fetch: releases: app does not support releases", f.getvalue())

    @patch.object(
        fetch,
        "fetch_fml_app",
        mock_fetch,
    )
    def test_fetch_releases(self):
        """Testing fetch_releases."""
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path="nimbus.fml.yaml",
            version_file=VersionFile.create_plain_text("version.txt"),
            branch_re=r"release_v(?P<major>\d)+",
            tag_re=r"v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)",
        )

        branches = [Ref(f"release_v{major}", f"branch-v{major}") for major in range(1, 7)]
        tags = [Ref(f"v{major}.0.0", f"tag-v{major}") for major in range(1, 7)]
        ref_versions = {
            **{f"branch-v{major}": Version(major, 0, 1) for major in range(1, 7)},
            **{f"tag-v{major}": Version(major) for major in range(1, 7)},
        }

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath(app_config.slug).mkdir()

            with mocks_for_fetch_releases(app_config, branches, tags, ref_versions):
                results = fetch_releases(manifest_dir, "app", app_config)

        self.assertEqual(len(results), 10)  # 5 branches and 5 tags
        for major in range(2, 7):
            self.assertIn(
                FetchResult(
                    app_name="app",
                    ref=Ref(f"v{major}.0.0", f"tag-v{major}"),
                    version=Version(major),
                ),
                results,
            )
            self.assertIn(
                FetchResult(
                    app_name="app",
                    ref=Ref(f"release_v{major}", f"branch-v{major}"),
                    version=Version(major, 0, 1),
                ),
                results,
            )

    @patch.object(
        fetch,
        "fetch_fml_app",
        mock_fetch,
    )
    def test_fetch_releases_no_tag_re(self):
        """Testing fetch_releases with no tag_re specified."""
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path="nimbus.fml.yaml",
            version_file=VersionFile.create_plain_text("version.txt"),
            branch_re=r"release_v(?P<major>\d)+",
        )

        branches = [Ref(f"release_v{major}", f"branch-v{major}") for major in range(1, 7)]
        ref_versions = {f"branch-v{major}": Version(major, 0, 1) for major in range(1, 7)}

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath(app_config.slug).mkdir()

            with mocks_for_fetch_releases(app_config, branches, None, ref_versions) as (
                get_branches,
                get_tags,
                resolve_ref_versions,
            ):
                results = fetch_releases(manifest_dir, "app", app_config)

                get_tags.assert_not_called()

        self.assertEqual(len(results), 5)  # 5 branches
        for major in range(2, 7):
            self.assertIn(
                FetchResult(
                    app_name="app",
                    ref=Ref(f"release_v{major}", f"branch-v{major}"),
                    version=Version(major, 0, 1),
                ),
                results,
            )

    @patch.object(fetch.github_api, "get_branches", lambda *args: [])
    def test_fetch_releases_no_major_release(self):
        """Testing fetch_releases when there are no release branches."""
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path="nimbus.fml.yaml",
            version_file=VersionFile.create_plain_text("version.txt"),
            branch_re=r"release_v(?P<major>\d)+",
            tag_re=r"v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)",
        )

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath(app_config.slug).mkdir()

            with self.assertRaisesRegex(
                Exception, "Could not find a major release for app."
            ):
                fetch_releases(manifest_dir, "app", app_config)
