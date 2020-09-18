import json
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.tests.factories import NimbusExperimentFactory


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

        response = self.client.get(
            reverse("visualization-analysis-data", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)
        self.assertEqual({}, json_data)

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
        DATA_ROW = {"point": 12, "upper": 13, "lower": 10}
        FULL_DATA = {"daily": DATA_ROW, "weekly": DATA_ROW}

        class File:
            def read(self):
                return json.dumps(DATA_ROW)

        mock_open.return_value = File()
        mock_exists.return_value = True
        experiment = NimbusExperimentFactory.create(status=status)

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
