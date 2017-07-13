from django.core.exceptions import ValidationError
from django.test import TestCase

from experimenter.experiments.models import ExperimentVariant
from experimenter.experiments.tests.factories import ExperimentFactory


class TestExperimentModel(TestCase):

    def test_invalid_addon_versions_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            ExperimentFactory.create_with_variants(addon_versions='invalid')

    def test_control_property_returns_experiment_control(self):
        experiment = ExperimentFactory.create_with_variants()
        control = ExperimentVariant.objects.get(
            experiment=experiment, is_control=True)
        self.assertEqual(experiment.control, control)

    def test_variant_property_returns_experiment_variant(self):
        experiment = ExperimentFactory.create_with_variants()
        variant = ExperimentVariant.objects.get(
            experiment=experiment, is_control=False)
        self.assertEqual(experiment.variant, variant)

    def test_is_begun_property_is_false_for_not_started(self):
        experiment = ExperimentFactory.create_with_variants()
        self.assertFalse(experiment.is_begun)

    def test_is_begun_property_is_true_for_started(self):
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()
        self.assertTrue(experiment.is_begun)

    def test_is_begun_property_is_true_for_complete(self):
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()
        experiment.status = experiment.EXPERIMENT_COMPLETE
        experiment.save()
        self.assertTrue(experiment.is_begun)

    def test_is_complete_property_is_false_for_not_started(self):
        experiment = ExperimentFactory.create_with_variants()
        self.assertFalse(experiment.is_complete)

    def test_is_complete_property_is_false_for_started(self):
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()
        self.assertFalse(experiment.is_complete)

    def test_is_complete_property_is_true_for_complete(self):
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()
        experiment.status = experiment.EXPERIMENT_COMPLETE
        experiment.save()
        self.assertTrue(experiment.is_complete)

    def test_setting_status_from_not_started_to_started_sets_start_date(self):
        experiment = ExperimentFactory.create()
        self.assertEqual(experiment.status, experiment.EXPERIMENT_NOT_STARTED)
        self.assertEqual(experiment.is_complete, False)
        self.assertIsNotNone(experiment.created_date)
        self.assertIsNone(experiment.start_date)
        self.assertIsNone(experiment.end_date)

        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()

        self.assertEqual(experiment.status, experiment.EXPERIMENT_STARTED)
        self.assertEqual(experiment.is_complete, False)
        self.assertIsNotNone(experiment.created_date)
        self.assertIsNotNone(experiment.start_date)
        self.assertIsNone(experiment.end_date)

    def test_setting_status_from_started_to_complete_sets_end_date(self):
        experiment = ExperimentFactory.create()
        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()

        self.assertEqual(experiment.status, experiment.EXPERIMENT_STARTED)
        self.assertIsNotNone(experiment.created_date)
        self.assertIsNotNone(experiment.start_date)
        self.assertIsNone(experiment.end_date)

        experiment.status = experiment.EXPERIMENT_COMPLETE
        experiment.save()

        self.assertEqual(experiment.status, experiment.EXPERIMENT_COMPLETE)
        self.assertEqual(experiment.is_complete, True)
        self.assertIsNotNone(experiment.created_date)
        self.assertIsNotNone(experiment.start_date)
        self.assertIsNotNone(experiment.end_date)

    def test_setting_from_started_to_not_started_raises_validation_error(self):
        experiment = ExperimentFactory.create()
        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()

        with self.assertRaises(ValidationError):
            experiment.status = experiment.EXPERIMENT_NOT_STARTED
            experiment.save()

    def test_setting_status_from_not_started_to_rejected(self):
        experiment = ExperimentFactory.create()
        experiment.status = experiment.EXPERIMENT_REJECTED
        experiment.save()

    def test_setting_status_from_started_to_rejected(self):
        experiment = ExperimentFactory.create()
        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()

        experiment.status = experiment.EXPERIMENT_REJECTED
        experiment.save()

    def test_setting_status_from_complete_to_rejected(self):
        experiment = ExperimentFactory.create()
        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()

        experiment.status = experiment.EXPERIMENT_COMPLETE
        experiment.save()

        experiment.status = experiment.EXPERIMENT_REJECTED
        experiment.save()

    def test_setting_status_from_invalid_to_rejected(self):
        experiment = ExperimentFactory.create()
        experiment.status = experiment.EXPERIMENT_INVALID
        experiment.save()

        experiment.status = experiment.EXPERIMENT_REJECTED
        experiment.save()

    def test_setting_status_from_not_started_to_invalid(self):
        experiment = ExperimentFactory.create()
        experiment.status = experiment.EXPERIMENT_INVALID
        experiment.save()

    def test_setting_status_from_started_to_invalid(self):
        experiment = ExperimentFactory.create()
        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()

        experiment.status = experiment.EXPERIMENT_INVALID
        experiment.save()

    def test_setting_status_from_complete_to_invalid(self):
        experiment = ExperimentFactory.create()
        experiment.status = experiment.EXPERIMENT_STARTED
        experiment.save()

        experiment.status = experiment.EXPERIMENT_COMPLETE
        experiment.save()

        experiment.status = experiment.EXPERIMENT_INVALID
        experiment.save()

    def test_setting_status_from_rejected_to_invalid(self):
        experiment = ExperimentFactory.create()

        experiment.status = experiment.EXPERIMENT_REJECTED
        experiment.save()

        experiment.status = experiment.EXPERIMENT_INVALID
        experiment.save()
