from django.core.exceptions import ValidationError
from django.test import TestCase

from experimenter.experiments.models import (
    Experiment, ExperimentVariant)
from experimenter.experiments.tests.factories import (
    ExperimentFactory, ExperimentChangeLogFactory)


class TestExperimentModel(TestCase):

    def test_start_date_returns_none_if_change_is_missing(self):
        experiment = ExperimentFactory.create_with_variants()
        self.assertEqual(experiment.start_date, None)

    def test_start_date_returns_datetime_if_change_exists(self):
        change = ExperimentChangeLogFactory.create(
            old_status=Experiment.STATUS_ACCEPTED,
            new_status=Experiment.STATUS_LAUNCHED,
        )
        self.assertEqual(change.experiment.start_date, change.changed_on)

    def test_end_date_returns_none_if_change_is_missing(self):
        experiment = ExperimentFactory.create_with_variants()
        self.assertEqual(experiment.end_date, None)

    def test_end_date_returns_datetime_if_change_exists(self):
        change = ExperimentChangeLogFactory.create(
            old_status=Experiment.STATUS_LAUNCHED,
            new_status=Experiment.STATUS_COMPLETE,
        )
        self.assertEqual(change.experiment.end_date, change.changed_on)

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

    def test_experiment_change_status_to_expected_status_allowed(self):
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_PENDING
        experiment.save()

    def test_experiment_change_status_to_unexpected_status_raises(self):
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_ACCEPTED

        with self.assertRaises(ValidationError):
            experiment.save()

    def test_experiment_with_created_status_is_not_readonly(self):
        experiment = ExperimentFactory.create_with_variants()
        self.assertFalse(experiment.is_readonly)

    def test_experiment_with_any_status_after_created_is_readonly(self):
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_PENDING
        experiment.save()
        self.assertTrue(experiment.is_readonly)
