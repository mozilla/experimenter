import json
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusProbeSetFactory,
)
from experimenter.visualization.api.v3.views import Significance


@override_settings(FEATURE_ANALYSIS=False)
class TestVisualizationView(TestCase):
    @parameterized.expand(
        [
            NimbusExperiment.Status.ACCEPTED,
            NimbusExperiment.Status.COMPLETE,
        ]
    )
    @patch("django.core.files.storage.default_storage.exists")
    def test_analysis_results_view_no_data(self, status, mock_exists):
        user_email = "user@example.com"

        mock_exists.return_value = False
        probe_set = NimbusProbeSetFactory.create()
        experiment = NimbusExperimentFactory.create_with_status(
            target_status=status, probe_sets=[probe_set]
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
                "weekly": None,
                "overall": None,
                "show_analysis": False,
            },
            json_data,
        )

    def add_probe_set_data(self, data, formatted_data, primary_probe_set):
        range_data = {
            "point": 4,
            "upper": 8,
            "lower": 2,
        }
        branches = ["control", "variant"]
        primary_metric = f"{primary_probe_set.slug}_ever_used"

        for branch in branches:
            formatted_data[branch]["branch_data"][primary_metric] = {
                "absolute": {**range_data, **{"count": 48}},
                "difference": {},
                "relative_uplift": {},
            }
            data.append(
                {
                    **range_data,
                    **{
                        "metric": primary_metric,
                        "branch": branch,
                        "statistic": "binomial",
                    },
                }
            )

    @parameterized.expand(
        [
            NimbusExperiment.Status.ACCEPTED,
            NimbusExperiment.Status.COMPLETE,
        ]
    )
    @patch("django.core.files.storage.default_storage.open")
    @patch("django.core.files.storage.default_storage.exists")
    def test_analysis_results_view_data(self, status, mock_exists, mock_open):
        user_email = "user@example.com"
        DATA_IDENTITY_ROW = {
            "point": 12,
            "upper": 13,
            "lower": 10,
            "metric": "identity",
            "statistic": "count",
        }
        CONTROL_DATA_ROW = {
            **DATA_IDENTITY_ROW,
            **{
                "branch": "control",
            },
        }
        VARIANT_DATA_ROW = {
            **DATA_IDENTITY_ROW,
            **{
                "branch": "variant",
            },
        }
        VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW = {
            **DATA_IDENTITY_ROW,
            **{
                "comparison": "difference",
                "metric": "search_count",
                "statistic": "mean",
                "branch": "variant",
            },
        }
        VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW = {
            **VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW,
            **{
                "point": -2,
                "upper": -1,
                "lower": -5,
                "metric": "retained",
                "statistic": "binomial",
            },
        }
        CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW = {
            **VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW,
            **{
                "point": 12,
                "upper": 13,
                "lower": -5,
                "branch": "control",
            },
        }
        DATA_WITHOUT_POPULATION_PERCENTAGE = [
            CONTROL_DATA_ROW,
            VARIANT_DATA_ROW,
            VARIANT_POSITIVE_SIGNIFICANCE_DATA_ROW,
            VARIANT_NEGATIVE_SIGNIFICANCE_DATA_ROW,
            CONTROL_NEUTRAL_SIGNIFICANCE_DATA_ROW,
        ]
        FORMATTED_DATA_WITH_POPULATION_PERCENTAGE = {
            "control": {
                "is_control": False,
                "branch_data": {
                    "identity": {
                        "absolute": {"lower": 10, "point": 12, "upper": 13},
                        "difference": {},
                        "relative_uplift": {},
                        "percent": 50,
                    },
                    "retained": {
                        "absolute": {},
                        "difference": {
                            "point": 12,
                            "upper": 13,
                            "lower": -5,
                        },
                        "relative_uplift": {},
                        "significance": Significance.NEUTRAL,
                    },
                },
            },
            "variant": {
                "is_control": False,
                "branch_data": {
                    "identity": {
                        "absolute": {"lower": 10, "point": 12, "upper": 13},
                        "difference": {},
                        "relative_uplift": {},
                        "percent": 50,
                    },
                    "search_count": {
                        "absolute": {},
                        "difference": {"lower": 10, "point": 12, "upper": 13},
                        "relative_uplift": {},
                        "significance": Significance.POSITIVE,
                    },
                    "retained": {
                        "absolute": {},
                        "difference": {
                            "point": -2,
                            "upper": -1,
                            "lower": -5,
                        },
                        "relative_uplift": {},
                        "significance": Significance.NEGATIVE,
                    },
                },
            },
        }

        FULL_DATA = {
            "daily": DATA_WITHOUT_POPULATION_PERCENTAGE,
            "weekly": DATA_WITHOUT_POPULATION_PERCENTAGE,
            "overall": FORMATTED_DATA_WITH_POPULATION_PERCENTAGE,
            "show_analysis": False,
        }

        class File:
            def read(self):
                return json.dumps(DATA_WITHOUT_POPULATION_PERCENTAGE)

        mock_open.return_value = File()
        mock_exists.return_value = True
        primary_probe_set = NimbusProbeSetFactory.create()
        experiment = NimbusExperimentFactory.create_with_status(
            target_status=status, probe_sets=[primary_probe_set]
        )
        experiment.probe_sets.add(
            NimbusProbeSetFactory.create(),
            through_defaults={"is_primary": False},
        )

        self.add_probe_set_data(
            DATA_WITHOUT_POPULATION_PERCENTAGE,
            FORMATTED_DATA_WITH_POPULATION_PERCENTAGE,
            primary_probe_set,
        )

        response = self.client.get(
            reverse("visualization-analysis-data", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        self.assertEqual(FULL_DATA, json_data)

    @parameterized.expand([NimbusExperiment.Status.ACCEPTED])
    def test_analysis_results_view_no_experiment(self, status):
        user_email = "user@example.com"
        response = self.client.get(
            reverse("visualization-analysis-data", kwargs={"slug": "fake_experiment"}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 404)

        json_data = json.loads(response.content)
        self.assertEqual({"detail": "Not found."}, json_data)
