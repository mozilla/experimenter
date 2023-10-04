from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from click.testing import CliRunner
import yaml

from manifesttool import cli
from manifesttool.appconfig import AppConfig, AppConfigs


# An AppConfig with a blank repo and fml_path so that the CLI cannot fetch
# anything.
APP_CONFIG = AppConfig(
    slug="app-slug",
    repo="",
    fml_path="",
)

APP_CONFIGS = AppConfigs(
    __root__={
        "app": APP_CONFIG,
    }
)


def generate_fml(app_config: AppConfig, channel: str) -> dict[str, any]:
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


class FetchLatestTests(TestCase):
    """Tests for the fetch-latest subcommand."""

    @patch.object(cli.github_api, "get_main_ref", side_effect=lambda *args: "ref")
    @patch.object(
        cli.nimbus_cli, "download_single_file", side_effect=mock_download_single_file
    )
    @patch.object(cli.nimbus_cli, "get_channels", side_effect=lambda *args: ["release"])
    def test_valid_manifest(self, get_channels, download_single_file, get_main_ref):
        """Test with a valid apps.yaml"""

        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("apps.yaml", "w") as f:
                yaml.dump(APP_CONFIGS.dict()["__root__"], f)

            result = runner.invoke(cli.main, ["--manifest-dir", ".", "fetch-latest"])
            self.assertEqual(result.exit_code, 0, result.exception or result.stdout)

            get_main_ref.assert_called_with(APP_CONFIG.repo)
            get_channels.assert_called_with(APP_CONFIG, "ref")
            download_single_file.assert_called_with(
                APP_CONFIG, "release", Path("."), "ref"
            )

            experimenter_manifest_path = Path(APP_CONFIG.slug, "experimenter.yaml")
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
