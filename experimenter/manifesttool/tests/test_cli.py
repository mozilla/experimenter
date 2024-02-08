import json
from contextlib import contextmanager
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import yaml
from click.testing import CliRunner

import manifesttool
from manifesttool.appconfig import (
    AppConfig,
    AppConfigs,
    DiscoveryStrategy,
    ReleaseDiscovery,
    Repository,
    RepositoryType,
    VersionFile,
)
from manifesttool.cli import main
from manifesttool.fetch import FetchResult
from manifesttool.repository import Ref, RefCache
from manifesttool.tests.test_fetch import FML_APP_CONFIG, LEGACY_APP_CONFIG, mock_fetch
from manifesttool.version import Version


def make_app_configs(app_configs: list[AppConfig]) -> AppConfigs:
    """Generate the AppConfigs for a single app."""
    return AppConfigs(
        __root__={
            app_config.slug.replace("-", "_"): app_config for app_config in app_configs
        }
    )


@contextmanager
def cli_runner(*, app_configs: AppConfig, manifest_path: Path = Path(".")):
    """Create a CliRunner with an isolated filesystem.

    The given AppConfigs will be written to disk before yielding the runner.
    """
    app_configs = make_app_configs(app_configs)
    runner = CliRunner()
    with runner.isolated_filesystem():
        with manifest_path.joinpath("apps.yaml").open("w") as f:
            # We can't use app_configs.dict() because it will not translate Enums to strings.
            as_json = app_configs.json()
            as_dict = json.loads(as_json)

            yaml.safe_dump(as_dict, f)

        yield runner


class CliTests(TestCase):
    """Tests for the command-line interface."""

    maxDiff = None

    @patch.object(manifesttool.cli, "fetch_releases")
    @patch.object(
        manifesttool.cli,
        "fetch_fml_app",
        side_effect=lambda *args: mock_fetch(*args, ref=Ref("main", "resolved")),
    )
    def test_fetch_fml(self, fetch_fml_app, fetch_releases):
        with cli_runner(app_configs=[FML_APP_CONFIG]) as runner:
            result = runner.invoke(main, ["--manifest-dir", ".", "fetch"])

        self.assertEqual(result.exit_code, 0, result.exception or result.stdout)

        fetch_fml_app.assert_called_with(
            Path("."),
            "fml_app",
            FML_APP_CONFIG,
        )

        self.assertIn(
            "SUMMARY:\n\nSUCCESS:\n\nfml_app at main (resolved) version None\n",
            result.stdout,
        )

        fetch_releases.assert_not_called()

    @patch.object(manifesttool.cli, "fetch_releases")
    @patch.object(
        manifesttool.cli,
        "fetch_fml_app",
        lambda *args: FetchResult(
            "fml_app", Ref("main"), version=None, exc=Exception("Connection error")
        ),
    )
    def test_fetch_fml_failure(self, fetch_releases):
        """Testing the fetch command with an FML app when a failure occurs."""
        with cli_runner(app_configs=[FML_APP_CONFIG]) as runner:
            result = runner.invoke(main, ["--manifest-dir", ".", "fetch"])

        self.assertEqual(result.exit_code, 1, result.exception or result.stdout)

        self.assertIn(
            "SUMMARY:\n\nFAILURES:\n\nfml_app at main version None\nConnection error\n",
            result.stdout,
        )

        fetch_releases.assert_not_called()

    @patch.object(manifesttool.cli, "fetch_releases")
    @patch.object(
        manifesttool.cli,
        "fetch_legacy_app",
        side_effect=lambda *args: FetchResult(
            "legacy_app", Ref("tip", "resolved"), version=None
        ),
    )
    def test_fetch_legacy(self, fetch_legacy_app, fetch_releases):
        """Testing the fetch command with a legacy app."""
        with cli_runner(app_configs=[LEGACY_APP_CONFIG]) as runner:
            result = runner.invoke(main, ["--manifest-dir", ".", "fetch"])

        self.assertEqual(result.exit_code, 0, result.exception or result.stdout)

        fetch_legacy_app.assert_called_with(
            Path("."),
            "legacy_app",
            LEGACY_APP_CONFIG,
        )

        self.assertIn(
            "SUMMARY:\n\nSUCCESS:\n\nlegacy_app at tip (resolved) version None\n",
            result.stdout,
        )

        fetch_releases.assert_not_called()

    @patch.object(manifesttool.cli, "fetch_releases")
    @patch.object(
        manifesttool.cli,
        "fetch_legacy_app",
        lambda *args: FetchResult(
            "legacy_app", Ref("tip"), version=None, exc=Exception("Connection error")
        ),
    )
    def test_fetch_legacy_failure(self, fetch_releases):
        """Testing the fetch command with a legacy app when a failure occurs."""
        with cli_runner(app_configs=[LEGACY_APP_CONFIG]) as runner:
            result = runner.invoke(main, ["--manifest-dir", ".", "fetch"])

        self.assertEqual(result.exit_code, 1, result.exception or result.stdout)

        self.assertIn(
            "SUMMARY:\n\nFAILURES:\n\nlegacy_app at tip version None\nConnection error\n",
            result.stdout,
        )

        fetch_releases.assert_not_called()

    @patch.object(
        manifesttool.cli,
        "fetch_fml_app",
        lambda *args: mock_fetch(*args, ref=Ref("main", "resolved")),
    )
    @patch.object(
        manifesttool.fetch,
        "discover_tagged_releases",
        lambda *args: {Version(1): Ref("foo", "bar")},
    )
    @patch.object(
        manifesttool.cli,
        "fetch_releases",
        wraps=manifesttool.cli.fetch_releases,
    )
    @patch.object(
        manifesttool.fetch,
        "fetch_fml_app",
        mock_fetch,
    )
    def test_fetch_fml_releases(self, fetch_releases):
        """Testing the fetch command with releases."""
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

        with cli_runner(app_configs=[app_config]) as runner:
            result = runner.invoke(main, ["--manifest-dir", ".", "fetch"])
            self.assertEqual(result.exit_code, 0, result.exception or result.stdout)

            cache_path = Path("fml-app", ".ref-cache.yaml")
            self.assertTrue(cache_path.exists(), "cli writes per-app ref cache")
            cache = RefCache.load_from_file(cache_path)

        self.assertEqual(cache, RefCache(__root__={"foo": "bar"}))

        # This is technically called with an empty cache, but the mock stores
        # the args it was called with. ``cache`` is an object, so when we update
        # ``cache`` inside ``fetch_releases``, we are also updating the same
        # object that the mock cached. Hence, we need to provide the filled out
        # cache to this assertion.
        fetch_releases.assert_called_once_with(
            Path("."),
            "fml_app",
            app_config,
            cache,
        )

    @patch.object(
        manifesttool.cli,
        "fetch_fml_app",
        lambda *args: FetchResult(
            "fml_app", ref=Ref("main", "quux"), version=None, exc=Exception("oh no")
        ),
    )
    @patch.object(
        manifesttool.fetch,
        "discover_tagged_releases",
        lambda *args: {
            Version(1): Ref("foo", "bar"),
            Version(2): Ref("baz", "qux"),
        },
    )
    @patch.object(manifesttool.fetch, "fetch_fml_app", lambda *args: mock_fetch(*args))
    @patch.object(
        manifesttool.fetch.RefCache,
        "load_or_create",
        lambda *args: RefCache(__root__={"foo": "bar"}),
    )
    def test_fetch_summary_filename(self):
        app_config = AppConfig(
            slug="fml-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="fml-repo",
            ),
            fml_path="nimbus.fml.yaml",
            release_discovery=ReleaseDiscovery(
                version_file=VersionFile.create_plain_text("version.txt"),
                strategies=[DiscoveryStrategy.create_tagged(branch_re="")],
            ),
        )

        with cli_runner(app_configs=[app_config]) as runner:
            result = runner.invoke(
                main, ["--manifest-dir", ".", "fetch", "--summary", "summary.txt"]
            )
            self.assertEqual(result.exit_code, 0, result.exception or result.stdout)

            with Path("summary.txt").open() as f:
                summary = f.read()

        self.assertEqual(
            summary,
            "SUMMARY:\n\n"
            "SUCCESS:\n\n"
            "fml_app at baz (qux) version 2.0.0\n\n"
            "CACHED:\n\n"
            "fml_app at foo (bar) version 1.0.0 (cached)\n\n"
            "FAILURES:\n\n"
            "fml_app at main (quux) version None\n"
            "oh no\n\n",
        )

    @patch.object(
        manifesttool.cli,
        "fetch_fml_app",
        side_effect=lambda *args: mock_fetch(*args, ref=Ref("main", "resolved")),
    )
    @patch.object(manifesttool.cli, "fetch_legacy_app")
    def test_fetch_specific_apps(self, fetch_legacy_app, fetch_fml_app):
        with cli_runner(app_configs=[LEGACY_APP_CONFIG, FML_APP_CONFIG]) as runner:
            result = runner.invoke(
                main, ["--manifest-dir", ".", "fetch", "--app", "fml_app"]
            )

        self.assertEqual(result.exit_code, 0, result.exception or result.stdout)

        fetch_legacy_app.assert_not_called()
        fetch_fml_app.assert_called_once_with(Path("."), "fml_app", FML_APP_CONFIG)

        self.assertIn(
            "SUMMARY:\n\n" "SUCCESS:\n\n" "fml_app at main (resolved) version None\n\n",
            result.stdout,
        )

        self.assertNotIn("CACHED:", result.stdout)
        self.assertNotIn("FAILURES:", result.stdout)

    def test_fetch_app_does_not_existt(self):
        with cli_runner(app_configs=[LEGACY_APP_CONFIG]) as runner:
            result = runner.invoke(
                main, ["--manifest-dir", ".", "fetch", "--app", "does_not_exist"]
            )

        self.assertEqual(result.exit_code, 1, result.exception or result.stdout)

        self.assertIn("fetch: unknown app does_not_exist", result.stdout)
        self.assertNotIn("SUMMARY", result.stdout)
