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
from experimenter.visualization.tests.api.constants import TestConstants


@override_settings(FEATURE_ANALYSIS=False)
class TestVisualizationView(TestCase):
    maxDiff = None

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

    def add_probe_set_data(
        self, data, formatted_data_with_pop, formatted_data_without_pop, primary_probe_set
    ):
        range_data = {
            "point": 4,
            "upper": 8,
            "lower": 2,
        }
        branches = ["control", "variant"]
        primary_metric = f"{primary_probe_set.slug}_ever_used"

        for branch in branches:
            formatted_data_with_pop[branch]["branch_data"][primary_metric] = {
                "absolute": {
                    "first": {**range_data, **{"count": 48}},
                    "all": [{**range_data, **{"count": 48}}],
                },
                "difference": {"all": [], "first": {}},
                "relative_uplift": {"all": [], "first": {}},
            }
            formatted_data_without_pop[branch]["branch_data"][primary_metric] = {
                "absolute": {
                    "first": {**range_data, **{"window_index": "1"}},
                    "all": [{**range_data, **{"window_index": "1"}}],
                },
                "difference": {"all": [], "first": {}},
                "relative_uplift": {"all": [], "first": {}},
            }
            data.append(
                {
                    **range_data,
                    **{
                        "metric": primary_metric,
                        "branch": branch,
                        "statistic": "binomial",
                        "window_index": "1",
                    },
                }
            )

    def add_all_probe_set_data(
        self,
        data,
        formatted_data_with_pop,
        formatted_data_without_pop,
        primary_probe_sets,
    ):
        for probe_set in primary_probe_sets:
            self.add_probe_set_data(
                data, formatted_data_with_pop, formatted_data_without_pop, probe_set
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

        (
            DATA_WITHOUT_POPULATION_PERCENTAGE,
            FORMATTED_DATA_WITHOUT_POPULATION_PERCENTAGE,
            FORMATTED_DATA_WITH_POPULATION_PERCENTAGE,
        ) = TestConstants.get_test_data()

        FULL_DATA = {
            "daily": DATA_WITHOUT_POPULATION_PERCENTAGE,
            "weekly": FORMATTED_DATA_WITHOUT_POPULATION_PERCENTAGE,
            "overall": FORMATTED_DATA_WITH_POPULATION_PERCENTAGE,
            "other_metrics": {"some_count": "Some Count"},
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

        self.add_all_probe_set_data(
            DATA_WITHOUT_POPULATION_PERCENTAGE,
            FORMATTED_DATA_WITH_POPULATION_PERCENTAGE,
            FORMATTED_DATA_WITHOUT_POPULATION_PERCENTAGE,
            experiment.primary_probe_sets,
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
