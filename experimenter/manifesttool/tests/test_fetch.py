import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Optional
from unittest import TestCase
from unittest.mock import call, patch

import responses
import yaml
from parameterized import parameterized

import manifesttool
from manifesttool.appconfig import (
    AppConfig,
    DiscoveryStrategy,
    ReleaseDiscovery,
    Repository,
    RepositoryType,
    VersionFile,
)
from manifesttool.fetch import (
    FetchResult,
    fetch_fml_app,
    fetch_legacy_app,
    fetch_releases,
    summarize_results,
)
from manifesttool.nimbus_cli import _get_experimenter_yaml_path, _get_fml_path
from manifesttool.repository import Ref, RefCache
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
        default_branch="tip",
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
    fml_path: str,
    channel: str,
    ref: str,
    version: Optional[Version],
):
    """A mock version of `nimbus fml -- single file`."""
    filename = _get_fml_path(manifest_dir, app_config, channel, version)
    with filename.open("w") as f:
        yaml.dump(generate_fml(app_config, channel), f)


DEFAULT_MOCK_FETCHES = {
    LEGACY_MANIFEST_PATH: LEGACY_MANIFEST,
    FEATURE_JSON_SCHEMA_PATH: FEATURE_JSON_SCHEMA,
}


def make_mock_fetch_file(
    *,
    ref: Optional[str] = None,
    paths_by_ref: Optional[dict[str, dict[str, str]]] = None,
):
    """Create a mock for hgmo_api.fetch_file

    Args:
        ref:
            If provided, the mock will only support fetching at the given
            resolved ref and it will only support fetching the files listed in
            ``DEFAULT_MOCK_FETCHES``.

            Mutually exclusive with ``paths_by_ref``.

        paths_by_ref:
            A mapping of resolved refs to file paths to contents.

            Mutually exclusive with ``ref``.
    """
    if ref is not None or paths_by_ref is not None:
        if ref is not None and paths_by_ref is not None:
            raise ValueError(
                "make_mock_fetch_file expects only one of paths_by_ref or ref"
            )

        if ref is not None:
            paths_by_ref = {
                ref: DEFAULT_MOCK_FETCHES,
            }
    else:
        raise ValueError("mack_mock_fetch_file requires one of paths_by_ref or ref")

    def mock_fetch_file(
        repo: str,
        file_path: str,
        rev: str,
        download_path: Optional[Path] = None,
    ) -> Optional[str]:
        """A mock version of hgmo_api.fetch_file."""
        try:
            paths = paths_by_ref[rev]
        except KeyError:
            raise Exception(f"Unexpected ref {rev} passed to hgmo_api.fetch_file")

        try:
            content = paths[file_path]
        except KeyError as e:
            raise Exception(
                f"Unexpected file path ({file_path}) passed to hgmo_api.fetch_file"
            ) from e

        if download_path:
            with download_path.open("w", newline="\n") as f:
                json.dump(content, f)
            return None

        return content

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
        manifesttool.fetch.github_api,
        "resolve_branch",
        side_effect=lambda *args: Ref("main", "ref"),
    )
    @patch.object(
        manifesttool.fetch.nimbus_cli,
        "download_single_file",
        side_effect=mock_download_single_file,
    )
    @patch.object(
        manifesttool.fetch.nimbus_cli,
        "get_channels",
        side_effect=lambda *args: ["release", "beta"],
    )
    def test_fetch_fml(self, get_channels, download_single_file, resolve_branch):
        """Testing fetch_fml_app."""
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("fml-app").mkdir()

            result = fetch_fml_app(manifest_dir, "app", FML_APP_CONFIG)
            self.assertIsNone(result.exc)

            resolve_branch.assert_called_with(FML_APP_CONFIG.repo.name, "main")
            get_channels.asset_called_with(FML_APP_CONFIG, "ref")
            download_single_file.assert_has_calls(
                [
                    call(
                        manifest_dir,
                        FML_APP_CONFIG,
                        FML_APP_CONFIG.fml_path,
                        "release",
                        "ref",
                        None,
                    ),
                    call(
                        manifest_dir,
                        FML_APP_CONFIG,
                        FML_APP_CONFIG.fml_path,
                        "beta",
                        "ref",
                        None,
                    ),
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

    @patch.object(manifesttool.fetch.github_api, "resolve_branch")
    @patch.object(
        manifesttool.fetch.nimbus_cli,
        "get_channels",
        side_effect=lambda *args: ["release"],
    )
    @patch.object(manifesttool.fetch.nimbus_cli, "download_single_file")
    @patch.object(manifesttool.fetch.nimbus_cli, "generate_experimenter_yaml")
    def test_fetch_fml_ref(
        self,
        generate_experimenter_yaml,
        download_single_file,
        get_channels,
        resolve_branch,
    ):
        """Testing fetch_fml_app with a specific ref."""
        ref = Ref("custom", "resolved")
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("fml-app").mkdir()

            result = fetch_fml_app(manifest_dir, "app", FML_APP_CONFIG, ref)
            self.assertIsNone(result.exc)

            resolve_branch.assert_not_called()
            get_channels.assert_called_with(
                FML_APP_CONFIG, FML_APP_CONFIG.fml_path, ref.target
            )
            download_single_file.assert_called_with(
                manifest_dir,
                FML_APP_CONFIG,
                FML_APP_CONFIG.fml_path,
                "release",
                ref.target,
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

    @patch.object(manifesttool.fetch.github_api, "resolve_branch")
    @patch.object(
        manifesttool.fetch.nimbus_cli,
        "get_channels",
        side_effect=lambda *args: ["release", "beta"],
    )
    @patch.object(
        manifesttool.fetch.nimbus_cli,
        "download_single_file",
        side_effect=mock_download_single_file,
    )
    @patch.object(
        manifesttool.fetch.nimbus_cli,
        "generate_experimenter_yaml",
        wraps=manifesttool.fetch.nimbus_cli.generate_experimenter_yaml,
    )
    def test_fetch_fml_ref_version(
        self,
        generate_experimenter_yaml,
        download_single_file,
        get_channels,
        resolve_branch,
    ):
        """Testing fetch_fml_app with a ref and a version."""
        ref = Ref("v123", "foo")
        version = Version(1, 2, 3)
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("fml-app").mkdir()

            result = fetch_fml_app(manifest_dir, "app", FML_APP_CONFIG, ref, version)
            self.assertEqual(result, FetchResult("app", ref, version))

            resolve_branch.assert_not_called()
            get_channels.assert_called_with(
                FML_APP_CONFIG, FML_APP_CONFIG.fml_path, ref.target
            )
            download_single_file.assert_has_calls(
                [
                    call(
                        manifest_dir,
                        FML_APP_CONFIG,
                        FML_APP_CONFIG.fml_path,
                        "release",
                        ref.target,
                        version,
                    ),
                    call(
                        manifest_dir,
                        FML_APP_CONFIG,
                        FML_APP_CONFIG.fml_path,
                        "beta",
                        ref.target,
                        version,
                    ),
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

    @parameterized.expand(
        [
            (["nimbus.fml.yaml", "app/nimbus.fml.yaml"], "nimbus.fml.yaml"),
            (["nimbus.fml.yaml", "app/nimbus.fml.yaml"], "app/nimbus.fml.yaml"),
        ]
    )
    @patch.object(
        manifesttool.fetch.github_api, "resolve_branch", lambda *args: Ref("main", "foo")
    )
    @patch.object(
        manifesttool.fetch.nimbus_cli,
        "get_channels",
        side_effect=lambda *args: ["channel"],
    )
    @patch.object(
        manifesttool.fetch.nimbus_cli,
        "download_single_file",
        side_effect=mock_download_single_file,
    )
    def test_fetch_fml_multiple_fml(
        self,
        fml_paths: list[str],
        correct_fml_path: str,
        download_single_file,
        get_channels,
    ):
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path=fml_paths,
        )

        def mock_file_exists(repo, file, rev):
            return file == correct_fml_path

        with (
            TemporaryDirectory() as tmp,
            patch.object(
                manifesttool.fetch.github_api, "file_exists", side_effect=mock_file_exists
            ) as file_exists,
        ):
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("fml-app").mkdir()

            result = fetch_fml_app(manifest_dir, "fml_app", app_config)
            self.assertEqual(
                result,
                FetchResult(
                    app_name="fml_app",
                    ref=Ref("main", "foo"),
                    version=None,
                ),
            )

            # Files are resolved in order, so file_exists() should be called index+1 times.
            index = fml_paths.index(correct_fml_path)
            self.assertEqual(file_exists.call_count, index + 1)
            file_exists.assert_has_calls(
                [call("fml-repo", fml_path, "foo") for fml_path in fml_paths[: index + 1]]
            )

        get_channels.assert_called_once_with(app_config, correct_fml_path, "foo")
        download_single_file.assert_called_once_with(
            manifest_dir,
            app_config,
            correct_fml_path,
            "channel",
            "foo",
            None,
        )

    @patch.object(
        manifesttool.fetch.github_api, "resolve_branch", lambda *args: Ref("main", "foo")
    )
    @patch.object(
        manifesttool.fetch.github_api, "file_exists", side_effect=lambda *args: False
    )
    @patch.object(manifesttool.fetch.nimbus_cli, "get_channels")
    def test_fetch_fml_missing_fml(self, get_channels, file_exists):
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path=[
                "does-not-exist.fml.yaml",
                "neither-does-this.fml.yaml",
            ],
        )

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("fml-app").mkdir()

            result = fetch_fml_app(manifest_dir, "fml_app", app_config)

        self.assertEqual(file_exists.call_count, 2)
        file_exists.assert_has_calls(
            [call("fml-repo", fml_path, "foo") for fml_path in app_config.fml_path]
        )

        self.assertIsNotNone(result.exc)
        self.assertEqual(
            str(result.exc), "Could not find a feature manifest for fml_app at main (foo)"
        )

        get_channels.assert_not_called()

    @patch.object(
        manifesttool.fetch.github_api,
        "resolve_branch",
        side_effect=Exception("Connection error"),
    )
    def test_fetch_fml_exception(self, resolve_branch):
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
                default_branch="tip",
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

    @patch.object(manifesttool.fetch.nimbus_cli, "download_single_file")
    @patch.object(manifesttool.fetch.nimbus_cli, "generate_experimenter_yaml")
    @patch.object(manifesttool.fetch.nimbus_cli, "get_channels", lambda *args: [])
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

    @patch.object(
        manifesttool.fetch.hgmo_api, "resolve_branch", lambda *args: Ref("tip", "ref")
    )
    @patch.object(
        manifesttool.fetch.hgmo_api,
        "fetch_file",
        side_effect=make_mock_fetch_file(ref="ref"),
    )
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

    @patch.object(manifesttool.fetch.hgmo_api, "resolve_branch")
    @patch.object(
        manifesttool.fetch.hgmo_api,
        "fetch_file",
        side_effect=make_mock_fetch_file(ref="resolved"),
    )
    def test_fetch_legacy_ref(self, fetch_file, resolve_branch):
        """Testing fetch_legacy_app with a specific ref."""
        ref = Ref("custom", "resolved")
        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("legacy-app").mkdir()

            result = fetch_legacy_app(manifest_dir, "app", LEGACY_APP_CONFIG, ref)
            self.assertIsNone(result.exc)

            resolve_branch.assert_not_called()
            fetch_file.assert_has_calls(
                [
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        LEGACY_MANIFEST_PATH,
                        ref.target,
                        manifest_dir / LEGACY_APP_CONFIG.slug / "experimenter.yaml",
                    ),
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        FEATURE_JSON_SCHEMA_PATH,
                        ref.target,
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

    @patch.object(manifesttool.fetch.hgmo_api, "resolve_branch")
    @patch.object(
        manifesttool.fetch.hgmo_api,
        "fetch_file",
        side_effect=make_mock_fetch_file(ref="foo"),
    )
    def test_fetch_legacy_ref_version(self, fetch_file, resolve_branch):
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

            resolve_branch.assert_not_called()
            fetch_file.assert_has_calls(
                [
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        LEGACY_MANIFEST_PATH,
                        ref.target,
                        manifest_dir
                        / LEGACY_APP_CONFIG.slug
                        / f"v{version}"
                        / "experimenter.yaml",
                    ),
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        FEATURE_JSON_SCHEMA_PATH,
                        ref.target,
                        manifest_dir
                        / LEGACY_APP_CONFIG.slug
                        / f"v{version}"
                        / "schemas"
                        / FEATURE_JSON_SCHEMA_PATH,
                    ),
                ]
            )

    @patch.object(
        manifesttool.fetch.hgmo_api, "resolve_branch", lambda *args: Ref("tip", "ref")
    )
    @patch.object(
        manifesttool.fetch.hgmo_api,
        "fetch_file",
        side_effect=make_mock_fetch_file(
            paths_by_ref={
                "ref": {
                    LEGACY_MANIFEST_PATH: {
                        "feature": LEGACY_MANIFEST["feature"],
                        "feature-2": LEGACY_MANIFEST["feature"],
                    },
                    FEATURE_JSON_SCHEMA_PATH: FEATURE_JSON_SCHEMA,
                }
            },
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
        manifesttool.fetch.hgmo_api,
        "resolve_branch",
        side_effect=Exception("Connection error"),
    )
    def test_fetch_legacy_exception(self, resolve_branch):
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

    def test_fetch_releases_unsupported_apps(self):
        """Testing fetch_releases with unsupported apps."""
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path="nimbus.fml.yaml",
        )

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            manifest_dir.joinpath(app_config.slug).mkdir()

            with self.assertRaisesRegex(Exception, "App app does not support releases."):
                fetch_releases(manifest_dir, "app", app_config, RefCache())

    @patch.object(
        manifesttool.fetch,
        "discover_tagged_releases",
        lambda *args: {
            Version(1): Ref("branch", "foo"),
            Version(1, 2, 3): Ref("tag", "bar"),
        },
    )
    @patch.object(
        manifesttool.fetch,
        "fetch_fml_app",
        side_effect=mock_fetch,
    )
    def test_fetch_releases_tagged(self, fetch_fml_app):
        """Testing fetch_releases with a TaggedDiscoveryStrategy."""
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path="nimbus.fml.yaml",
            release_discovery=ReleaseDiscovery(
                version_file=VersionFile.create_plain_text("version.txt"),
                strategies=[DiscoveryStrategy.create_tagged(branch_re="", tag_re="")],
            ),
        )

        cache = RefCache()

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)

            results = fetch_releases(manifest_dir, "fml_app", app_config, cache)

        self.assertEqual(fetch_fml_app.call_count, 2)
        fetch_fml_app.assert_has_calls(
            [
                call(
                    manifest_dir,
                    "fml_app",
                    app_config,
                    Ref("branch", "foo"),
                    Version(1),
                ),
                call(
                    manifest_dir,
                    "fml_app",
                    app_config,
                    Ref("tag", "bar"),
                    Version(1, 2, 3),
                ),
            ]
        )

        self.assertEqual(
            cache,
            RefCache(
                __root__={
                    "branch": "foo",
                    "tag": "bar",
                }
            ),
        )

        self.assertEqual(len(results), 2)
        self.assertIn(
            FetchResult(
                app_name="fml_app",
                ref=Ref("branch", "foo"),
                version=Version(1),
            ),
            results,
        )
        self.assertIn(
            FetchResult(
                app_name="fml_app",
                ref=Ref("tag", "bar"),
                version=Version(1, 2, 3),
            ),
            results,
        )

    @patch.object(
        manifesttool.fetch,
        "discover_branched_releases",
        lambda *args: {
            Version(1): Ref("tip", "foo"),
        },
    )
    @patch.object(
        manifesttool.fetch,
        "fetch_legacy_app",
        side_effect=mock_fetch,
    )
    def test_fetch_releases_branches(self, fetch_legacy_app):
        """Testing fetch_releases with a BranchedDiscoveryStrategy."""
        app_config = AppConfig(
            slug="legacy-app",
            repo=Repository(
                type=RepositoryType.HGMO,
                name="legacy-repo",
                default_branch="tip",
            ),
            experimenter_yaml_path="experimenter.yaml",
            release_discovery=ReleaseDiscovery(
                version_file=VersionFile.create_plain_text("version.txt"),
                strategies=[DiscoveryStrategy.create_branched()],
            ),
        )

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)
            results = fetch_releases(manifest_dir, "legacy_app", app_config, RefCache())

        fetch_legacy_app.assert_called_once_with(
            manifest_dir, "legacy_app", app_config, Ref("tip", "foo"), Version(1)
        )

        self.assertEqual(
            results,
            [
                FetchResult(
                    app_name="legacy_app",
                    ref=Ref("tip", "foo"),
                    version=Version(1),
                ),
            ],
        )

    @patch.object(
        manifesttool.fetch,
        "discover_tagged_releases",
        lambda *args: {
            Version(1): Ref("branch", "up-to-date-branch"),
            Version(1, 2, 3): Ref("tag", "up-to-date-tag"),
        },
    )
    @patch.object(manifesttool.fetch, "fetch_fml_app", side_effect=mock_fetch)
    def test_fetch_releases_cached(self, fetch_fml_app):
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path="nimbus.fml.yaml",
            release_discovery=ReleaseDiscovery(
                version_file=VersionFile.create_plain_text("version.txt"),
                strategies=[DiscoveryStrategy.create_tagged(branch_re="", tag_re="")],
            ),
        )

        cache = RefCache(
            __root__={
                "branch": "outdated-branch",
                "tag": "up-to-date-tag",
            }
        )

        with TemporaryDirectory() as tmp:
            manifest_dir = Path(tmp)

            fetch_releases(manifest_dir, "fml_app", app_config, cache)

        self.assertEqual(fetch_fml_app.call_count, 1)
        fetch_fml_app.called_once_with(
            manifest_dir,
            "fml_app",
            app_config,
            Ref("branch", "updated-branch"),
            Version(1),
        )

        self.assertEqual(
            cache,
            RefCache(
                __root__={
                    "branch": "up-to-date-branch",
                    "tag": "up-to-date-tag",
                }
            ),
        )

    def test_summarize_results(self):
        buffer = StringIO()

        summarize_results(
            [
                FetchResult(
                    "app-1",
                    Ref("a", "foo"),
                    None,
                ),
                FetchResult("app-2", Ref("b", "bar"), Version(1, 2, 3)),
                FetchResult("app-3", Ref("c", "baz"), None, exc=Exception("oh no")),
                FetchResult("app-4", Ref("d", "qux"), Version(4, 5, 6), cached=True),
                FetchResult(
                    "app-5",
                    Ref("e", "quux"),
                    Version(7, 8, 9),
                    exc=Exception("rats!"),
                ),
            ],
            buffer,
        )

        self.assertEqual(
            buffer.getvalue(),
            "SUMMARY:\n\n"
            "SUCCESS:\n\n"
            "app-1 at a (foo) version None\n"
            "app-2 at b (bar) version 1.2.3\n"
            "\n"
            "CACHED:\n\n"
            "app-4 at d (qux) version 4.5.6 (cached)\n"
            "\n"
            "FAILURES:\n\n"
            "app-3 at c (baz) version None\n"
            "oh no\n\n"
            "app-5 at e (quux) version 7.8.9\n"
            "rats!\n\n",
        )
