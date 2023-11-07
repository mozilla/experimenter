from unittest import TestCase
from pathlib import Path

from manifesttool.appconfig import AppConfig, Repository, RepositoryType
from manifesttool.fetch import fetch_fml_app, fetch_legacy_app
from manifesttool.repository import Ref


class FetchTests(TestCase):
    def test_fetch_fml_unresolved_ref(self):
        """Testing fetch_fml_app with an unresolved ref."""
        app_config = AppConfig(
            slug="slug",
            repo=Repository(
                type=RepositoryType.GITHUB,
                name="invalid",
            ),
            fml_path="nimbus.fml.yaml",
        ),

        with self.assertRaises(
            ValueError,
            msg="fetch_fml_app: ref `foo` is not resolved",
        ):
            fetch_fml_app(Path("."), "repo", app_config, Ref("foo"))

    def test_fetch_legacy_unresolved_ref(self):
        """Testing fetch_legacy_app with an unresolved ref."""
        app_config = AppConfig(
            slug="invalid",
            repo=Repository(
                type=RepositoryType.HGMO,
                name="invalid",
            ),
            experimenter_yaml_path="experimenter.yaml",
        )

        with self.assertRaises(
            ValueError,
            msg="fetch_legacy_app: ref `foo` is not resolved",
        ):
            fetch_fml_app(Path("."), "repo", app_config, Ref("foo"))
