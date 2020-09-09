from django.test import TestCase
from django.core.management import call_command

from experimenter.experiments.models import ExperimentCore
from experimenter.experiments.constants import ExperimentConstants


class TestInitialData(TestCase):
    def test_load_dummy_experiments(self):
        self.assertFalse(ExperimentCore.objects.exists())
        call_command("load_dummy_experiments")
        self.assertTrue(ExperimentCore.objects.exists())

    def test_load_dummy_experiments_with_specified_values(self):
        call_command(
            "load_dummy_experiments",
            num_of_experiments=20,
            status=ExperimentConstants.STATUS_DRAFT,
        )
        self.assertTrue(ExperimentCore.objects.exists())
        self.assertEqual(ExperimentCore.objects.count(), 20)
        self.assertEqual(
            ExperimentCore.objects.filter(
                status=ExperimentConstants.STATUS_DRAFT
            ).count(),
            20,
        )
