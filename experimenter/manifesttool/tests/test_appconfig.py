from unittest import TestCase

from manifesttool.appconfig import AppConfigs
from manifesttool.cli import MANIFEST_DIR


class AppConfigTests(TestCase):
    def test_parse_apps_yaml(self):
        """Testing that we can parse apps.yaml."""
        AppConfigs.load_from_directory(MANIFEST_DIR)

    def test_parse_experimenter_and_fml_paths(self):
        """Testing that parsing apps.yaml fails if an app contains both the
        fml_path and experimenter_yaml_path keys.
        """
        with self.assertRaises(ValueError):
            AppConfigs.parse_obj(
                {
                    "app": {
                        "slug": "app",
                        "repo": {"type": "github", "name": "owner/repo"},
                        "fml_path": "nimbus.fml.yaml",
                        "experimenter_yaml_path": "experimenter.yaml",
                    },
                }
            )

    def test_parse_no_paths(self):
        """Testing that parsing apps.yaml fails if an app is missing both the
        fml_path and experimenter_yaml_path keys.
        """
        with self.assertRaises(ValueError):
            AppConfigs.parse_obj(
                {
                    "app": {
                        "slug": "app",
                        "repo": {"type": "github", "name": "owner/repo"},
                    },
                }
            )
