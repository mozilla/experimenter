import json
from contextlib import contextmanager
from pathlib import Path
from unittest import TestCase
from unittest.mock import call, patch
from typing import Any

import yaml
from click.testing import CliRunner

from manifesttool import cli
from manifesttool.appconfig import AppConfig, AppConfigs, Repository, RepositoryType

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


def make_app_configs(app_config: AppConfig) -> AppConfigs:
    """Generate the AppConfigs for a single app."""
    return AppConfigs(
        __root__={
            app_config.slug.replace("-", "_"): app_config,
        }
    )


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
    app_config: AppConfig,
    channel: str,
    manifests_dir: Path,
    ref: str,
):
    """A mock version of `nimbus fml -- single file`."""

    filename = manifests_dir / app_config.slug / f"{channel}.fml.yaml"
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


@contextmanager
def cli_runner(*, app_config: AppConfig, manifest_path: Path = Path(".")):
    """Create a CliRunner with an isolated filesystem.

    The given AppConfigs will be written to disk before yielding the runner.
    """
    app_configs = make_app_configs(app_config)
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

    @patch.object(cli.github_api, "get_main_ref", side_effect=lambda *args: "ref")
    @patch.object(
        cli.nimbus_cli, "download_single_file", side_effect=mock_download_single_file
    )
    @patch.object(cli.nimbus_cli, "get_channels", side_effect=lambda *args: ["release"])
    def test_fetch_latest_fml(self, get_channels, download_single_file, get_main_ref):
        """Testing the fetch-latest subcommand with an FML app."""
        with cli_runner(app_config=FML_APP_CONFIG) as runner:
            result = runner.invoke(cli.main, ["--manifest-dir", ".", "fetch-latest"])
            self.assertEqual(result.exit_code, 0, result.exception or result.stdout)

            get_main_ref.assert_called_with(FML_APP_CONFIG.repo.name)
            get_channels.assert_called_with(FML_APP_CONFIG, "ref")
            download_single_file.assert_called_with(
                FML_APP_CONFIG, "release", Path("."), "ref"
            )

            experimenter_manifest_path = Path(FML_APP_CONFIG.slug, "experimenter.yaml")
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

    @patch.object(cli.github_api, "get_main_ref", lambda *args: "ref")
    @patch.object(cli.nimbus_cli, "download_single_file")
    @patch.object(cli.nimbus_cli, "generate_experimenter_yaml")
    @patch.object(cli.nimbus_cli, "get_channels", lambda *args: [])
    def test_fetch_latest_fml_no_channels(
        self, generate_experimenter_yaml, download_single_file
    ):
        """Testing the fetch-latest subcommand with an FML app that has no channels
        listed.
        """
        with cli_runner(app_config=FML_APP_CONFIG) as runner:
            result = runner.invoke(cli.main, ["--manifest-dir", ".", "fetch-latest"])
            self.assertEqual(result.exit_code, 0, result.exception or result.stdout)

            download_single_file.assert_not_called()
            generate_experimenter_yaml.assert_not_called()

            self.assertFalse(
                Path(FML_APP_CONFIG.slug, "experimenter.yaml").exists(),
                "experimenter.yaml should not be created",
            )

    @patch.object(cli.hgmo_api, "get_tip_rev", lambda *args: "ref")
    @patch.object(cli.hgmo_api, "fetch_file", side_effect=make_mock_fetch_file())
    def test_fetch_latest_legacy(self, fetch_file):
        """Testing the fetch-latest subcommand with a legacy app."""
        with cli_runner(app_config=LEGACY_APP_CONFIG) as runner:
            result = runner.invoke(cli.main, ["--manifest-dir", ".", "fetch-latest"])
            self.assertEqual(result.exit_code, 0, result.exception or result.stdout)

            fetch_file.assert_has_calls(
                [
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        LEGACY_MANIFEST_PATH,
                        "ref",
                        Path(LEGACY_APP_CONFIG.slug, "experimenter.yaml"),
                    ),
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        FEATURE_JSON_SCHEMA_PATH,
                        "ref",
                        Path(LEGACY_APP_CONFIG.slug, "schemas", FEATURE_JSON_SCHEMA_PATH),
                    ),
                ]
            )
            self.assertEqual(fetch_file.call_count, 2)

    @patch.object(cli.hgmo_api, "get_tip_rev", lambda *args: "ref")
    @patch.object(
        cli.hgmo_api,
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
        """Testing that the fetch-latest subcommand for a legacy app does not
        fetch the same schema twice.
        """
        with cli_runner(app_config=LEGACY_APP_CONFIG) as runner:
            result = runner.invoke(cli.main, ["--manifest-dir", ".", "fetch-latest"])
            self.assertEqual(result.exit_code, 0, result.exception or result.stdout)

            fetch_file.assert_has_calls(
                [
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        LEGACY_MANIFEST_PATH,
                        "ref",
                        Path(LEGACY_APP_CONFIG.slug, "experimenter.yaml"),
                    ),
                    call(
                        LEGACY_APP_CONFIG.repo.name,
                        FEATURE_JSON_SCHEMA_PATH,
                        "ref",
                        Path(LEGACY_APP_CONFIG.slug, "schemas", FEATURE_JSON_SCHEMA_PATH),
                    ),
                ]
            )
            self.assertEqual(fetch_file.call_count, 2)

    def test_fetch_legacy_github_unsupported(self):
        """Testing that the fetch-latest subcommand does not support a legacy
        app on a GitHub repository.
        """
        app_config = AppConfig(
            slug="invalid-app",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="invalid-repo",
            ),
            experimenter_yaml_path="experimenter.yaml",
        )

        with cli_runner(app_config=app_config) as runner:
            result = runner.invoke(cli.main, ["--manifest-dir", ".", "fetch-latest"])
            self.assertEqual(result.exit_code, 1, result.stdout)
            self.assertEqual(
                str(result.exception),
                "Legacy experimenter.yaml apps on GitHub are not supported.",
            )

    def test_fetch_fml_hgmo_unsupported(self):
        """Testing that the fetch-latest subcommand does not support a FML-based
        app on a hg.mozilla.org repository.
        """
        app_config = AppConfig(
            slug="invalid-app",
            repo=Repository(
                type=RepositoryType.HGMO,
                name="invalid-repo",
            ),
            fml_path="nimbus.fml.yaml",
        )

        with cli_runner(app_config=app_config) as runner:
            result = runner.invoke(cli.main, ["--manifest-dir", ".", "fetch-latest"])
            self.assertEqual(result.exit_code, 1, result.stdout)
            self.assertEqual(
                str(result.exception),
                "FML-based apps on hg.mozilla.org are not supported.",
            )
