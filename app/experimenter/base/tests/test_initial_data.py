from django.core.management import call_command
from django.test import TestCase

from experimenter.experiments.models import Experiment, NimbusExperiment


class TestInitialData(TestCase):
    def test_load_dummy_experiments(self):
        self.assertFalse(Experiment.objects.exists())
        self.assertFalse(NimbusExperiment.objects.exists())
        call_command("load_dummy_experiments")

        for status, _ in Experiment.STATUS_CHOICES:
            self.assertTrue(Experiment.objects.filter(status=status).exists())

        for application in NimbusExperiment.Application:
            for status in NimbusExperiment.Status:
                self.assertTrue(
                    NimbusExperiment.objects.filter(
                        status=status, application=application
                    ).exists()
                )
