import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from manifesttool import nimbus_cli
from manifesttool.appconfig import AppConfig

APP_CONFIG = AppConfig(slug="slug", repo="owner/repo", fml_path="path")


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
            nimbus_cli.get_channels(APP_CONFIG, "0" * 40), ["staging", "prod"]
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
        side_effect=lambda *args: "invalid json",
    )
    def test_get_channels_invalid(self):
        "Testing get_channels handling of invalid JSON." ""

        with self.assertRaises(json.decoder.JSONDecodeError):
            nimbus_cli.get_channels(APP_CONFIG, "channel")

    @patch.object(nimbus_cli.subprocess, "check_call")
    def test_download_single_file(self, mock_cli):
        """Tesing download_single_file calls nimbus-cli with correct arguments."""

        nimbus_cli.download_single_file(APP_CONFIG, "channel", Path("."), "0" * 40)

        mock_cli.assert_called_with(
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
                "slug/channel.fml.yaml",
            ]
        )

    @patch.object(nimbus_cli.subprocess, "check_call")
    def test_generate_experimenter_yaml(self, mock_cli):
        """Testing generate_experimenter_yaml calls nimbus-cli with correct arguments."""

        nimbus_cli.generate_experimenter_yaml(APP_CONFIG, "channel", Path("."))

        mock_cli.assert_called_with(
            [
                "/application-services/bin/nimbus-cli",
                "fml",
                "--",
                "generate-experimenter",
                "slug/channel.fml.yaml",
                "slug/experimenter.yaml",
            ]
        )
