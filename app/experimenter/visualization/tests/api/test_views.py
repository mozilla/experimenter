import json
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.tests.factories import NimbusExperimentFactory


@override_settings(FEATURE_ANALYSIS=False)
class TestVisualizationView(TestCase):
    @parameterized.expand(
        [
            ExperimentConstants.STATUS_ACCEPTED,
            ExperimentConstants.STATUS_COMPLETE,
        ]
    )
    @patch("django.core.files.storage.default_storage.exists")
    def test_analysis_results_view_no_data(self, status, mock_exists):
        user_email = "user@example.com"

        mock_exists.return_value = False
        experiment = NimbusExperimentFactory.create(status=status)
        feature_metric = f"{experiment.features[0]}_ever_used"

        response = self.client.get(
            reverse("visualization-analysis-data", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        self.assertEqual(
            {
                "daily": None,
                "weekly": None,
                "overall": None,
                "show_analysis": False,
                "result_map": {
                    "retained": "binomial",
                    "search_count": "mean",
                    "identity": "count",
                    feature_metric: "binomial",
                },
            },
            json_data,
        )

    @parameterized.expand(
        [
            ExperimentConstants.STATUS_ACCEPTED,
            ExperimentConstants.STATUS_COMPLETE,
        ]
    )
    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_analysis_results_view_data(self, status, mock_exists, mock_open):
        user_email = "user@example.com"
        CONTROL_DATA_ROW = {
            "point": 12,
            "upper": 13,
            "lower": 10,
            "metric": "identity",
            "statistic": "count",
            "branch": "control",
        }
        VARIANT_DATA_ROW = {
            "point": 12,
            "upper": 13,
            "lower": 10,
            "metric": "identity",
            "statistic": "count",
            "branch": "variant",
        }
        POPULATION_PERCENTAGE_CONTROL_ROW = {
            "point": 50,
            "metric": "identity",
            "statistic": "percentage",
            "branch": "control",
        }
        POPULATION_PERCENTAGE_VARIANT_ROW = {
            "point": 50,
            "metric": "identity",
            "statistic": "percentage",
            "branch": "variant",
        }
        DATA_WITHOUT_POPULATION_PERCENTAGE = [CONTROL_DATA_ROW, VARIANT_DATA_ROW]
        DATA_WITH_POPULATION_PERCENTAGE = [
            CONTROL_DATA_ROW,
            VARIANT_DATA_ROW,
            POPULATION_PERCENTAGE_CONTROL_ROW,
            POPULATION_PERCENTAGE_VARIANT_ROW,
        ]
        FULL_DATA = {
            "daily": DATA_WITHOUT_POPULATION_PERCENTAGE,
            "weekly": DATA_WITHOUT_POPULATION_PERCENTAGE,
            "overall": DATA_WITH_POPULATION_PERCENTAGE,
            "show_analysis": False,
            "result_map": {
                "retained": "binomial",
                "search_count": "mean",
                "identity": "count",
            },
        }

        class File:
            def read(self):
                return json.dumps(DATA_WITHOUT_POPULATION_PERCENTAGE)

        mock_open.return_value = File()
        mock_exists.return_value = True
        experiment = NimbusExperimentFactory.create(status=status)

        feature_metric = f"{experiment.features[0]}_ever_used"
        FULL_DATA["result_map"][feature_metric] = "binomial"

        response = self.client.get(
            reverse("visualization-analysis-data", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        self.assertEqual(FULL_DATA, json_data)

    @parameterized.expand([ExperimentConstants.STATUS_ACCEPTED])
    def test_analysis_results_view_no_experiment(self, status):
        user_email = "user@example.com"
        response = self.client.get(
            reverse("visualization-analysis-data", kwargs={"slug": "fake_experiment"}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 404)

        json_data = json.loads(response.content)
        self.assertEqual({"detail": "Not found."}, json_data)
