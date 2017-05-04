from django.test import TestCase

from experimenter.experiments.models import ExperimentVariant
from experimenter.experiments.tests.factories import ExperimentFactory


class TestExperimentModel(TestCase):

    def test_variant_and_control_properties(self):
        experiment = ExperimentFactory.create_with_variants()
        variant = ExperimentVariant.objects.filter(experiment=experiment, is_control=False)
        control = ExperimentVariant.objects.filter(experiment=experiment, is_control=True)
        self.assertEqual(experiment.variant, variant)
        self.assertEqual(experiment.control, control)
