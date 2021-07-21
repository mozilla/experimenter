import datetime
import json
from unittest.mock import patch

from django.test import TestCase, override_settings
from parameterized import parameterized

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.jetstream import tasks
from experimenter.jetstream.models import (
    BranchComparisonData,
    DataPoint,
    Group,
    JetstreamDataPoint,
    MetricData,
    SignificanceData,
)
from experimenter.jetstream.tests import mock_valid_outcomes
from experimenter.jetstream.tests.constants import TestConstants
from experimenter.outcomes import Outcomes


@mock_valid_outcomes
@override_settings(FEATURE_ANALYSIS=False)
class TestFetchJetstreamDataTask(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        Outcomes.clear_cache()

    def get_metric_data(self, data_point):
        return MetricData(
            absolute=BranchComparisonData(first=data_point, all=[data_point]),
            difference=BranchComparisonData(),
            relative_uplift=BranchComparisonData(),
            significance=SignificanceData(),
        ).dict(exclude_none=True)

    def add_outcome_data(self, data, overall_data, weekly_data, primary_outcome):
        primary_metrics = ["mozilla_default_browser", "default_browser_action"]
        range_data = DataPoint(lower=2, point=4, upper=8)

        for primary_metric in primary_metrics:
            for branch in ["control", "variant"]:
                if Group.OTHER not in overall_data[branch]["branch_data"]:
                    overall_data[branch]["branch_data"][Group.OTHER] = {}
                if Group.OTHER not in weekly_data[branch]["branch_data"]:
                    weekly_data[branch]["branch_data"][Group.OTHER] = {}

                data_point_overall = range_data.copy()
                data_point_overall.count = 48.0
                overall_data[branch]["branch_data"][Group.OTHER][
                    primary_metric
                ] = self.get_metric_data(data_point_overall)

                data_point_weekly = range_data.copy()
                data_point_weekly.window_index = "1"
                weekly_data[branch]["branch_data"][Group.OTHER][
                    primary_metric
                ] = self.get_metric_data(data_point_weekly)

                data.append(
                    JetstreamDataPoint(
                        **range_data.dict(exclude_none=True),
                        metric=primary_metric,
                        branch=branch,
                        statistic="binomial",
                        window_index="1",
                    ).dict(exclude_none=True)
                )

    def add_all_outcome_data(
        self,
        data,
        overall_data,
        weekly_data,
        primary_outcomes,
    ):
        for primary_outcome in primary_outcomes:
            self.add_outcome_data(data, overall_data, weekly_data, primary_outcome)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_results_data_not_null(self, lifecycle, mock_exists, mock_open):
        (
            DAILY_DATA,
            WEEKLY_DATA,
            OVERALL_DATA,
        ) = TestConstants.get_test_data()

        FULL_DATA = {
            "daily": DAILY_DATA,
            "weekly": WEEKLY_DATA,
            "overall": OVERALL_DATA,
            "other_metrics": {
                Group.OTHER: {
                    "some_count": "Some Count",
                    "another_count": "Another Count",
                },
            },
            "metadata": {},
            "show_analysis": False,
        }

        class File:
            def __init__(self, filename):
                self.name = filename

            def read(self):
                if "metadata" in self.name:
                    return "{}"
                return json.dumps(DAILY_DATA)

        def open_file(filename):
            return File(filename)

        mock_open.side_effect = open_file
        mock_exists.return_value = True
        primary_outcome = "default-browser"
        secondary_outcome = "secondary_outcome"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            primary_outcomes=[primary_outcome],
            secondary_outcomes=[secondary_outcome],
        )

        self.add_all_outcome_data(
            DAILY_DATA,
            OVERALL_DATA,
            WEEKLY_DATA,
            experiment.primary_outcomes,
        )

        tasks.fetch_experiment_data(experiment.id)
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.results_data, FULL_DATA)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("django.core.files.storage.default_storage.exists")
    def test_results_data_null(self, lifecycle, mock_exists):
        mock_exists.return_value = False
        primary_outcome = "default-browser"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, primary_outcomes=[primary_outcome]
        )

        tasks.fetch_experiment_data(experiment.id)
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(
            experiment.results_data,
            {
                "daily": None,
                "metadata": None,
                "overall": None,
                "show_analysis": False,
                "weekly": None,
            },
        )

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_fetch_in_loop(self, lifecycle, mock_delay):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        tasks.fetch_jetstream_data()
        mock_delay.assert_called_once_with(experiment.id)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_expired_in_loop(self, lifecycle, mock_delay):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        experiment.results_data = {
            "daily": None,
            "metadata": None,
            "overall": None,
            "show_analysis": False,
            "weekly": None,
        }
        experiment.save()
        experiment.changes.all().filter(
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
        ).update(changed_on=datetime.date.today() - datetime.timedelta(days=4))
        tasks.fetch_jetstream_data()
        mock_delay.assert_not_called()

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_data_null_fetches(self, lifecycle, mock_delay):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        experiment.changes.all().filter(
            old_status=NimbusExperiment.Status.LIVE,
            new_status=NimbusExperiment.Status.COMPLETE,
        ).update(changed_on=datetime.date.today() - datetime.timedelta(days=4))
        tasks.fetch_jetstream_data()
        mock_delay.assert_called_once_with(experiment.id)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
        ]
    )
    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_no_data_fetch_in_loop(self, lifecycle, mock_delay):
        NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        tasks.fetch_jetstream_data()
        mock_delay.assert_not_called()

    @patch("experimenter.jetstream.tasks.fetch_experiment_data.delay")
    def test_exception_for_fetch_jetstream_data(self, mock_delay):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
        )
        mock_delay.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.fetch_jetstream_data()

    @patch("experimenter.jetstream.tasks.get_experiment_data")
    def test_exception_for_fetch_experiment_data(self, mock_get_experiment_data):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
        )
        mock_get_experiment_data.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.fetch_experiment_data(experiment.id)
