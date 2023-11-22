import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import call, patch

from parameterized import parameterized

from manifesttool import nimbus_cli
from manifesttool.appconfig import AppConfig, Repository, RepositoryType
from manifesttool.version import Version

APP_CONFIG = AppConfig(
    slug="slug",
    repo=Repository(
        type=RepositoryType.GITHUB,
        name="owner/repo",
    ),
    fml_path="path",
)


class NimbusCliTests(TestCase):
    """Tests for nimbus_cli."""

    @patch.object(
        nimbus_cli.subprocess,
        "check_output",
        return_value=json.dumps(["staging", "prod"]),
    )
    def test_get_channels(self, mock_cli):
        """Testing get_channels calls nimbus-cli with correct arguments."""
        self.assertEqual(
            nimbus_cli.get_channels(APP_CONFIG, APP_CONFIG.fml_path, "0" * 40),
            ["staging", "prod"],
        )
        mock_cli.assert_called_with(
            [
                "/application-services/bin/nimbus-cli",
                "fml",
                "--",
                "channels",
                "--json",
                "--ref",
                "0" * 40,
                "@owner/repo/path",
            ],
        )

    @patch.object(
        nimbus_cli.subprocess,
        "check_output",
        lambda *args: "invalid json",
    )
    def test_get_channels_invalid(self):
        "Testing get_channels handling of invalid JSON."
        with self.assertRaises(json.decoder.JSONDecodeError):
            nimbus_cli.get_channels(APP_CONFIG, APP_CONFIG.fml_path, "channel")

    @parameterized.expand(
        [
            (None, "slug/channel.fml.yaml"),
            (Version(1), "slug/v1.0.0/channel.fml.yaml"),
            (Version(1, 1), "slug/v1.1.0/channel.fml.yaml"),
            (Version(1, 1, 1), "slug/v1.1.1/channel.fml.yaml"),
        ]
    )
    def test_download_single_file(self, version, fml_path):
        """Tesing download_single_file calls nimbus-cli with correct arguments."""
        with (
            TemporaryDirectory() as tmp,
            patch.object(nimbus_cli.subprocess, "check_call") as check_call,
        ):
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("slug").mkdir()
            nimbus_cli.download_single_file(
                manifest_dir,
                APP_CONFIG,
                APP_CONFIG.fml_path,
                "channel",
                "0" * 40,
                version,
            )

            check_call.assert_called_with(
                [
                    "/application-services/bin/nimbus-cli",
                    "fml",
                    "--",
                    "single-file",
                    "--channel",
                    "channel",
                    "--ref",
                    "0" * 40,
                    "@owner/repo/path",
                    str(manifest_dir / fml_path),
                ]
            )

    @parameterized.expand(
        [
            (None, "slug/channel.fml.yaml", "slug/experimenter.yaml"),
            (Version(1), "slug/v1.0.0/channel.fml.yaml", "slug/v1.0.0/experimenter.yaml"),
            (
                Version(1, 1),
                "slug/v1.1.0/channel.fml.yaml",
                "slug/v1.1.0/experimenter.yaml",
            ),
            (
                Version(1, 1, 1),
                "slug/v1.1.1/channel.fml.yaml",
                "slug/v1.1.1/experimenter.yaml",
            ),
        ]
    )
    def test_generate_experimenter_yaml(
        self, version: Version, fml_path: str, experimenter_yaml_path: str
    ):
        """Testing generate_experimenter_yaml calls nimbus-cli with correct arguments."""
        with (
            TemporaryDirectory() as tmp,
            patch.object(nimbus_cli.subprocess, "check_call") as check_call,
        ):
            manifest_dir = Path(tmp)
            manifest_dir.joinpath("slug").mkdir()
            nimbus_cli.generate_experimenter_yaml(
                manifest_dir, APP_CONFIG, "channel", version
            )

            check_call.assert_called_with(
                [
                    "/application-services/bin/nimbus-cli",
                    "fml",
                    "--",
                    "generate-experimenter",
                    str(manifest_dir / fml_path),
                    str(manifest_dir / experimenter_yaml_path),
                ]
            )
