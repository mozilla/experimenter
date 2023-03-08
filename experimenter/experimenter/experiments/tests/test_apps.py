from django.apps import apps
from django.test import TestCase

from experimenter.experiments.apps import ExperimentsConfig


class AppTests(TestCase):
    def test_app_config(self):
        with self.settings(INSTALLED_APPS=["experimenter.experiments"]):
            config = apps.get_app_config("experiments")
        self.assertIsInstance(config, ExperimentsConfig)
