from django.core.management import call_command
from django.test import TestCase

from experimenter.experiments.models import Experiment, NimbusExperiment


class TestInitialData(TestCase):
    def test_load_dummy_experiments(self):
        self.assertFalse(Experiment.objects.exists())
        self.assertFalse(NimbusExperiment.objects.exists())
        call_command("load_dummy_experiments")
        self.assertEqual(Experiment.objects.count(), len(Experiment.STATUS_CHOICES))
        self.assertEqual(
            NimbusExperiment.objects.count(), len(NimbusExperiment.Status.choices)
        )
