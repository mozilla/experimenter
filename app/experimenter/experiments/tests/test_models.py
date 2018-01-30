import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from experimenter.projects.tests.factories import ProjectFactory
from experimenter.experiments.models import (
    Experiment, ExperimentVariant)
from experimenter.experiments.tests.factories import (
    ExperimentFactory, ExperimentChangeLogFactory)


class TestExperimentManager(TestCase):

    def test_most_recently_changed_orders_by_latest_changes(self):
        now = datetime.datetime.now()
        experiment1 = ExperimentFactory.create_with_variants()
        experiment2 = ExperimentFactory.create_with_variants()

        ExperimentChangeLogFactory.create(
            experiment=experiment1,
            old_status=None,
            new_status=Experiment.STATUS_CREATED,
            changed_on=(now - datetime.timedelta(days=2)),
        )

        ExperimentChangeLogFactory.create(
            experiment=experiment2,
            old_status=None,
            new_status=Experiment.STATUS_CREATED,
            changed_on=(now - datetime.timedelta(days=1)),
        )

        self.assertEqual(
            list(Experiment.objects.most_recently_changed()),
            [experiment2, experiment1],
        )

        ExperimentChangeLogFactory.create(
            experiment=experiment1,
            old_status=experiment1.status,
            new_status=Experiment.STATUS_PENDING,
        )

        self.assertEqual(
            list(Experiment.objects.most_recently_changed()),
            [experiment1, experiment2],
        )


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

    def test_experiment_status_validation_raises_if_enabled(self):
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_ACCEPTED

        with self.assertRaises(ValidationError):
            experiment.save(validate=True)

    def test_experiment_status_validation_should_not_raise_if_disabled(self):
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_ACCEPTED

        experiment.save()

    def test_experiment_status_validation_should_not_raise_for_new_exp(self):
        project = ProjectFactory.create()
        experiment = ExperimentFactory.build(project=project)
        experiment.status = experiment.STATUS_ACCEPTED

        experiment.save(validate=True)

    def test_experiment_with_created_status_is_not_readonly(self):
        experiment = ExperimentFactory.create_with_variants()
        self.assertFalse(experiment.is_readonly)

    def test_experiment_with_any_status_after_created_is_readonly(self):
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_PENDING
        experiment.save()
        self.assertTrue(experiment.is_readonly)

    def test_experiment_population_returns_correct_string(self):
        experiment = ExperimentFactory(
            population_percent='0.5',
            firefox_version='57.0',
            firefox_channel='Nightly',
        )
        self.assertEqual(
            experiment.population,
            '0.5% of Firefox 57.0 Nightly'
        )

    def test_experiment_variants_returns_correct_string(self):
        experiment = ExperimentFactory.create_with_variants()

        experiment.control.name = 'Control'
        experiment.control.ratio = 1
        experiment.control.save()

        experiment.variant.name = 'Variant'
        experiment.variant.ratio = 1
        experiment.variant.save()

        self.assertEqual(
            experiment.variant_ratios,
            '1 Variant : 1 Control',
        )

    def test_experiments_viewer_link_is_correct(self):
        experiment = ExperimentFactory.create(slug='experiment')
        self.assertEqual(
            experiment.experiments_viewer_url,
            ('https://moz-experiments-viewer.herokuapp.com/?ds=experiment'
             '&metrics=ALL&next=%2F&pop=ALL&scale=linear&showOutliers=false'),
        )

    def test_accept_url_is_correct(self):
        experiment = ExperimentFactory.create(slug='experiment')
        self.assertEqual(
            experiment.accept_url,
            'https://localhost/api/v1/experiments/experiment/accept/',
        )

    def test_reject_url_is_correct(self):
        experiment = ExperimentFactory.create(slug='experiment')
        self.assertEqual(
            experiment.reject_url,
            'https://localhost/api/v1/experiments/experiment/reject/',
        )


class TestExperimentChangeLogManager(TestCase):

    def test_latest_returns_most_recent_changelog(self):
        now = datetime.datetime.now()
        experiment = ExperimentFactory.create_with_variants()

        changelog1 = ExperimentChangeLogFactory.create(
            experiment=experiment,
            old_status=None,
            new_status=Experiment.STATUS_CREATED,
            changed_on=(now - datetime.timedelta(days=2)),
        )

        self.assertEqual(experiment.changes.latest(), changelog1)

        changelog2 = ExperimentChangeLogFactory.create(
            experiment=experiment,
            old_status=Experiment.STATUS_CREATED,
            new_status=Experiment.STATUS_PENDING,
            changed_on=(now - datetime.timedelta(days=1)),
        )

        self.assertEqual(experiment.changes.latest(), changelog2)
