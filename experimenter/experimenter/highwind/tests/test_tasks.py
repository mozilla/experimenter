import datetime
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from pydantic import ValidationError

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.highwind.client import UnsupportedSchemaError, blob_path
from experimenter.highwind.tasks import (
    fetch_highwind_data,
    get_analysis_experiments,
)
from experimenter.highwind.tests.factories import build_analysis


@mock.patch("experimenter.highwind.tasks.list_analysis_blobs")
class TestGetAnalysisExperiments(TestCase):
    def test_includes_an_experiment_the_job_wrote_a_blob_for(self, mock_list):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE
        )
        mock_list.return_value = {blob_path(experiment.slug)}

        self.assertIn(experiment, get_analysis_experiments())

    def test_excludes_an_experiment_with_no_blob(self, mock_list):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE
        )
        mock_list.return_value = set()

        self.assertNotIn(experiment, get_analysis_experiments())

    def test_state_and_dates_do_not_decide_it(self, mock_list):
        draft = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        long_completed = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        long_completed.update_computed_end_date(
            timezone.now().date() - datetime.timedelta(days=365)
        )
        long_completed.save()
        mock_list.return_value = {
            blob_path(draft.slug),
            blob_path(long_completed.slug),
        }

        experiments = get_analysis_experiments()

        self.assertIn(draft, experiments)
        self.assertIn(long_completed, experiments)

    def test_a_blob_with_no_experiment_is_ignored(self, mock_list):
        mock_list.return_value = {blob_path("an-experiment-we-do-not-have")}

        self.assertEqual(get_analysis_experiments().count(), 0)


@mock.patch("experimenter.highwind.tasks.get_analysis")
@mock.patch("experimenter.highwind.tasks.list_analysis_blobs")
class TestFetchHighwindData(TestCase):
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            analysis_data=None,
        )
        self.generated_at = timezone.now()

    def written(self, *experiments):
        return {blob_path(experiment.slug) for experiment in experiments}

    def test_loads_analysis_for_an_experiment_with_none_stored(
        self, mock_list, mock_get_analysis
    ):
        mock_list.return_value = self.written(self.experiment)
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

    def test_loads_analysis_generated_after_the_stored_one(
        self, mock_list, mock_get_analysis
    ):
        self.experiment.analysis_data = {"stale": True}
        self.experiment.analysis_last_updated = self.generated_at - datetime.timedelta(
            days=1
        )
        self.experiment.save()
        mock_list.return_value = self.written(self.experiment)
        mock_get_analysis.return_value = build_analysis(
            self.experiment.slug, self.generated_at
        )

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.analysis_last_updated, self.generated_at)
        self.assertNotIn("stale", self.experiment.analysis_data)

    def test_skips_analysis_no_newer_than_the_stored_one(
        self, mock_list, mock_get_analysis
    ):
        stored = {"metadata": {"experiment_slug": self.experiment.slug}}
        self.experiment.analysis_data = stored
        self.experiment.analysis_last_updated = self.generated_at
        self.experiment.save()
        mock_list.return_value = self.written(self.experiment)
        mock_get_analysis.return_value = build_analysis(
            self.experiment.slug, self.generated_at - datetime.timedelta(hours=1)
        )

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.analysis_last_updated, self.generated_at)
        self.assertEqual(self.experiment.analysis_data, stored)

    def test_skips_an_experiment_with_no_blob(self, mock_list, mock_get_analysis):
        mock_list.return_value = self.written(self.experiment)
        mock_get_analysis.return_value = None

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        self.assertIsNone(self.experiment.analysis_data)
        self.assertIsNone(self.experiment.analysis_last_updated)

    def test_skips_a_blob_that_analysed_another_experiment(
        self, mock_list, mock_get_analysis
    ):
        mock_list.return_value = self.written(self.experiment)
        mock_get_analysis.return_value = build_analysis(
            "a-different-experiment", self.generated_at
        )

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        self.assertIsNone(self.experiment.analysis_data)
        self.assertIsNone(self.experiment.analysis_last_updated)

    @mock.patch("experimenter.highwind.tasks.sentry_sdk.capture_exception")
    def test_unsupported_schema_is_not_reported(
        self, mock_capture, mock_list, mock_get_analysis
    ):
        stored = {"metadata": {"experiment_slug": self.experiment.slug}}
        self.experiment.analysis_data = stored
        self.experiment.analysis_last_updated = self.generated_at
        self.experiment.save()
        mock_list.return_value = self.written(self.experiment)
        mock_get_analysis.side_effect = UnsupportedSchemaError("no schema version")

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.analysis_data, stored)
        self.assertEqual(self.experiment.analysis_last_updated, self.generated_at)
        mock_capture.assert_not_called()

    @mock.patch("experimenter.highwind.tasks.sentry_sdk.capture_exception")
    def test_validation_failure_reports_without_overwriting(
        self, mock_capture, mock_list, mock_get_analysis
    ):
        stored = {"metadata": {"experiment_slug": self.experiment.slug}}
        self.experiment.analysis_data = stored
        self.experiment.analysis_last_updated = self.generated_at
        self.experiment.save()
        mock_list.return_value = self.written(self.experiment)
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
        self, mock_capture, mock_list, mock_get_analysis
    ):
        other = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            analysis_data=None,
        )
        mock_list.return_value = self.written(self.experiment, other)

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

    def test_writes_no_changelog(self, mock_list, mock_get_analysis):
        mock_list.return_value = self.written(self.experiment)
        mock_get_analysis.return_value = build_analysis(
            self.experiment.slug, self.generated_at
        )
        changes_before = self.experiment.changes.count()

        fetch_highwind_data()

        self.assertEqual(self.experiment.changes.count(), changes_before)

    def test_does_not_move_the_experiment_to_the_top_of_recently_updated(
        self, mock_list, mock_get_analysis
    ):
        mock_list.return_value = self.written(self.experiment)
        mock_get_analysis.return_value = build_analysis(
            self.experiment.slug, self.generated_at
        )
        updated_before = NimbusExperiment.objects.get(
            id=self.experiment.id
        )._updated_date_time

        fetch_highwind_data()

        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment._updated_date_time, updated_before)

    def test_checks_only_the_experiments_with_a_blob(self, mock_list, mock_get_analysis):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE
        )
        mock_list.return_value = self.written(self.experiment)
        mock_get_analysis.return_value = None

        fetch_highwind_data()

        self.assertEqual(mock_get_analysis.call_count, 1)
