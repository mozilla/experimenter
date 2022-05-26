from django.core.management import call_command
from django.test import TestCase

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.legacy.legacy_experiments.models import Experiment


class TestInitialData(TestCase):
    def test_load_dummy_experiments(self):
        self.assertFalse(Experiment.objects.exists())
        self.assertFalse(NimbusExperiment.objects.exists())
        call_command("load_dummy_experiments")

        for status, _ in Experiment.STATUS_CHOICES:
            self.assertTrue(Experiment.objects.filter(status=status).exists())

        for lifecycle in NimbusExperimentFactory.LocalLifecycles:
            states = lifecycle.value
            final_state = states[-1].value
            self.assertTrue(NimbusExperiment.objects.filter(**final_state).exists())
