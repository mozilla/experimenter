import datetime
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from mozilla_nimbus_schemas.highwind import HighwindAnalysis
from pydantic import ValidationError

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.highwind import tasks
from experimenter.highwind.tasks import (
    COMPLETED_LOOKBACK_DAYS,
    fetch_highwind_data,
    get_analysis_experiments,
)
from experimenter.highwind.tests import build_analysis_json


def build_analysis(slug, generated_at):
    return HighwindAnalysis.model_validate_json(build_analysis_json(slug, generated_at))


class TestGetAnalysisExperiments(TestCase):
    def setUp(self):
        super().setUp()
        self.as_of = datetime.date(2026, 10, 15)

    def test_includes_live_experiments(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE
        )

        self.assertIn(experiment, get_analysis_experiments(self.as_of))

    def test_includes_recently_completed_experiments(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        experiment.update_computed_end_date(
            self.as_of - datetime.timedelta(days=COMPLETED_LOOKBACK_DAYS - 1)
        )
        experiment.save()

        self.assertIn(experiment, get_analysis_experiments(self.as_of))

    def test_excludes_experiments_completed_before_the_lookback(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        experiment.update_computed_end_date(
            self.as_of - datetime.timedelta(days=COMPLETED_LOOKBACK_DAYS + 1)
        )
        experiment.save()

        self.assertNotIn(experiment, get_analysis_experiments(self.as_of))

    def test_excludes_drafts(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )

        self.assertNotIn(experiment, get_analysis_experiments(self.as_of))


@mock.patch("experimenter.highwind.tasks.get_analysis")
class TestFetchHighwindData(TestCase):
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE
        )
        self.generated_at = timezone.now()

    def test_loads_analysis_for_an_experiment_with_none_stored(self, mock_get_analysis):
        mock_get_analysis.return_value = build_analysis(
            self.experiment.slug, self.generated_at
        )

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.analysis_last_updated, self.generated_at)
        self.assertEqual(
            self.experiment.analysis_data["metadata"]["experiment_slug"],
            self.experiment.slug,
        )

    def test_loads_analysis_generated_after_the_stored_one(self, mock_get_analysis):
        self.experiment.analysis_data = {"stale": True}
        self.experiment.analysis_last_updated = self.generated_at - datetime.timedelta(
            days=1
        )
        self.experiment.save()
        mock_get_analysis.return_value = build_analysis(
            self.experiment.slug, self.generated_at
        )

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.analysis_last_updated, self.generated_at)
        self.assertNotIn("stale", self.experiment.analysis_data)

    def test_skips_analysis_no_newer_than_the_stored_one(self, mock_get_analysis):
        stored = {"metadata": {"experiment_slug": self.experiment.slug}}
        self.experiment.analysis_data = stored
        self.experiment.analysis_last_updated = self.generated_at
        self.experiment.save()
        mock_get_analysis.return_value = build_analysis(
            self.experiment.slug, self.generated_at - datetime.timedelta(hours=1)
        )

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.analysis_last_updated, self.generated_at)
        self.assertEqual(self.experiment.analysis_data, stored)

    def test_skips_an_experiment_with_no_blob(self, mock_get_analysis):
        mock_get_analysis.return_value = None

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        self.assertIsNone(self.experiment.analysis_data)
        self.assertIsNone(self.experiment.analysis_last_updated)

    @mock.patch("experimenter.highwind.tasks.sentry_sdk.capture_exception")
    def test_validation_failure_reports_without_overwriting(
        self, mock_capture, mock_get_analysis
    ):
        stored = {"metadata": {"experiment_slug": self.experiment.slug}}
        self.experiment.analysis_data = stored
        self.experiment.analysis_last_updated = self.generated_at
        self.experiment.save()
        mock_get_analysis.side_effect = ValidationError.from_exception_data(
            "HighwindAnalysis", []
        )

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.analysis_data, stored)
        self.assertEqual(self.experiment.analysis_last_updated, self.generated_at)
        mock_capture.assert_called_once()

    @mock.patch("experimenter.highwind.tasks.sentry_sdk.capture_exception")
    def test_one_failing_experiment_does_not_block_the_others(
        self, mock_capture, mock_get_analysis
    ):
        other = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE
        )

        def analysis_or_raise(experiment):
            if experiment.slug == self.experiment.slug:
                raise Exception("gcs is down")
            return build_analysis(experiment.slug, self.generated_at)

        mock_get_analysis.side_effect = analysis_or_raise

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        other.refresh_from_db()
        self.assertIsNone(self.experiment.analysis_data)
        self.assertEqual(other.analysis_last_updated, self.generated_at)
        mock_capture.assert_called_once()

    def test_writes_no_changelog(self, mock_get_analysis):
        mock_get_analysis.return_value = build_analysis(
            self.experiment.slug, self.generated_at
        )
        changes_before = self.experiment.changes.count()

        fetch_highwind_data()

        self.assertEqual(self.experiment.changes.count(), changes_before)

    def test_does_not_move_the_experiment_to_the_top_of_recently_updated(
        self, mock_get_analysis
    ):
        mock_get_analysis.return_value = build_analysis(
            self.experiment.slug, self.generated_at
        )
        updated_before = NimbusExperiment.objects.get(
            id=self.experiment.id
        )._updated_date_time

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment._updated_date_time, updated_before)

    def test_checks_each_selected_experiment(self, mock_get_analysis):
        mock_get_analysis.return_value = None
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )

        fetch_highwind_data()

        self.assertEqual(
            mock_get_analysis.call_count, tasks.get_analysis_experiments().count()
        )
