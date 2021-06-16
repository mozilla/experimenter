import json
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory


@override_settings(FEATURE_ANALYSIS=False)
class TestVisualizationView(TestCase):
    maxDiff = None

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.CREATED,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    @patch("django.core.files.storage.default_storage.exists")
    def test_analysis_results_view_200(self, lifecycle, mock_exists):
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

    @parameterized.expand([NimbusExperiment.Status.DRAFT])
    def test_analysis_results_view_404(self, status):
        user_email = "user@example.com"
        response = self.client.get(
            reverse("visualization-analysis-data", kwargs={"slug": "fake_experiment"}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 404)

        json_data = json.loads(response.content)
        self.assertEqual({"detail": "Not found."}, json_data)
