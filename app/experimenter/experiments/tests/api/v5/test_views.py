from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.api.v5.serializers import NimbusExperimentCSVSerializer
from experimenter.experiments.api.v5.views import NimbusExperimentCSVRenderer
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.tests.factories.nimbus import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


class TestNimbusExperimentCSVListView(TestCase):
    def test_get_returns_csv_info(self):
        user_email = "user@example.com"
        application = NimbusConstants.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment_1 = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config]
        )
        experiment_2 = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config]
        )
        response = self.client.get(
            reverse("nimbus-experiments-api-csv"),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        csv_data = response.content
        expected_csv_data = NimbusExperimentCSVRenderer().render(
            NimbusExperimentCSVSerializer([experiment_1, experiment_2], many=True).data,
            renderer_context={"header": NimbusExperimentCSVSerializer.Meta.fields},
        )
        self.assertEqual(csv_data, expected_csv_data)
