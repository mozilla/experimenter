import json
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.visualization.api.v3.models import (
    BranchComparisonData,
    DataPoint,
    JetstreamDataPoint,
    MetricData,
    SignificanceData,
)
from experimenter.visualization.tests.api.constants import TestConstants


@override_settings(FEATURE_ANALYSIS=False)
class TestVisualizationView(TestCase):
    maxDiff = None

    @parameterized.expand(
        [
            (NimbusExperiment.Lifecycles.CREATED,),
            (NimbusExperiment.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("django.core.files.storage.default_storage.exists")
    def test_analysis_results_view_no_data(self, lifecycle, mock_exists):
        user_email = "user@example.com"

        mock_exists.return_value = False
        primary_outcome = "outcome"
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, primary_outcomes=[primary_outcome]
        )

        response = self.client.get(
            reverse("visualization-analysis-data", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        self.assertEqual(
            {
                "daily": None,
                "metadata": None,
                "weekly": None,
                "overall": None,
                "show_analysis": False,
            },
            json_data,
        )

    def get_metric_data(self, data_point):
        return MetricData(
            absolute=BranchComparisonData(first=data_point, all=[data_point]),
            difference=BranchComparisonData(),
            relative_uplift=BranchComparisonData(),
            significance=SignificanceData(),
        ).dict(exclude_none=True)

    def add_outcome_data(self, data, overall_data, weekly_data, primary_outcome):
        range_data = DataPoint(lower=2, point=4, upper=8)
        primary_metric = f"{primary_outcome}_ever_used"

        for branch in ["control", "variant"]:
            data_point_overall = range_data.copy()
            data_point_overall.count = 48.0
            overall_data[branch]["branch_data"][primary_metric] = self.get_metric_data(
                data_point_overall
            )

            data_point_weekly = range_data.copy()
            data_point_weekly.window_index = "1"
            weekly_data[branch]["branch_data"][primary_metric] = self.get_metric_data(
                data_point_weekly
            )

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
            (NimbusExperiment.Lifecycles.CREATED,),
            (NimbusExperiment.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_analysis_results_view_data(self, lifecycle, mock_exists, mock_open):
        user_email = "user@example.com"

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
                "some_count": "Some Count",
                "another_count": "Another Count",
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
        primary_outcome = "primary_outcome"
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

        response = self.client.get(
            reverse("visualization-analysis-data", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        self.assertEqual(FULL_DATA, json_data)

    @parameterized.expand([NimbusExperiment.Status.DRAFT])
    def test_analysis_results_view_no_experiment(self, status):
        user_email = "user@example.com"
        response = self.client.get(
            reverse("visualization-analysis-data", kwargs={"slug": "fake_experiment"}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 404)

        json_data = json.loads(response.content)
        self.assertEqual({"detail": "Not found."}, json_data)
