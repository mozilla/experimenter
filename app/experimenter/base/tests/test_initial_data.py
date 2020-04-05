from django.test import TestCase
from django.core.management import call_command

from experimenter.base.models import Country, Locale
from experimenter.experiments.models import Experiment
from experimenter.experiments.constants import ExperimentConstants


class TestInitialData(TestCase):
    def test_load_locales_countries(self):
        self.assertTrue(not Country.objects.exists())
        self.assertTrue(not Locale.objects.exists())

        call_command("load-countries")

        self.assertTrue(Country.objects.exists())

        # First mess with the installed data, so it tests the "corrections"
        # that the managemeent does.
        Country.objects.filter(code="SV").delete()
        Country.objects.filter(code="FR").update(name="Frankies")

        call_command("load-countries")

        self.assertTrue(Country.objects.get(code="SV"))
        self.assertEqual(Country.objects.get(code="FR").name, "France")

    def test_load_dummy_experiments(self):
        self.assertFalse(Experiment.objects.exists())
        call_command("load-dummy-experiments")
        self.assertTrue(Experiment.objects.exists())

    def test_load_dummy_experiments_with_specified_values(self):
        call_command(
            "load-dummy-experiments",
            num_of_experiments=20,
            status=ExperimentConstants.STATUS_DRAFT,
        )
        self.assertTrue(Experiment.objects.exists())
        self.assertEqual(Experiment.objects.count(), 20)
        self.assertEqual(
            Experiment.objects.filter(status=ExperimentConstants.STATUS_DRAFT).count(), 20
        )
