import datetime

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.api.v5.serializers import (
    NimbusConfigurationDataClass,
    NimbusConfigurationSerializer,
    NimbusExperimentCsvSerializer,
)
from experimenter.experiments.api.v5.views import NimbusExperimentCsvRenderer
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusChangeLogFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


class TestNimbusExperimentCsvListView(TestCase):
    def test_get_returns_csv_info_sorted_by_start_date(self):
        user_email = "user@example.com"
        application = NimbusConstants.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment_1 = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config]
        )
        NimbusChangeLogFactory.create(
            experiment=experiment_1,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date(2022, 5, 1),
        )
        experiment_2 = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config]
        )
        NimbusChangeLogFactory.create(
            experiment=experiment_2,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date(2020, 5, 1),
        )

        experiment_3 = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config]
        )

        experiment_4 = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config]
        )
        NimbusChangeLogFactory.create(
            experiment=experiment_4,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date(2021, 5, 1),
        )
        response = self.client.get(
            reverse("nimbus-experiments-csv"),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        csv_data = response.content
        expected_csv_data = NimbusExperimentCsvRenderer().render(
            NimbusExperimentCsvSerializer(
                [experiment_1, experiment_4, experiment_2, experiment_3], many=True
            ).data,
            renderer_context={"header": NimbusExperimentCsvSerializer.Meta.fields},
        )

        self.assertEqual(csv_data, expected_csv_data)

    def test_get_returns_csv_filter_archived_experimentes_info(self):
        user_email = "user@example.com"
        application = NimbusConstants.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment_1 = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config]
        )
        NimbusChangeLogFactory.create(
            experiment=experiment_1,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date(2019, 5, 1),
        )
        # Archived experiment
        NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config], is_archived=True
        )
        response = self.client.get(
            reverse("nimbus-experiments-csv"),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        csv_data = response.content
        expected_csv_data = NimbusExperimentCsvRenderer().render(
            NimbusExperimentCsvSerializer([experiment_1], many=True).data,
            renderer_context={"header": NimbusExperimentCsvSerializer.Meta.fields},
        )
        self.assertEqual(csv_data, expected_csv_data)


class TestNimbusConfigurationView(TestCase):
    def test_nimbus_configuration_view_returns_config_data(self):
        user_email = "user@example.com"
        response = self.client.get(
            reverse("nimbus-api-config"),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            NimbusConfigurationSerializer(NimbusConfigurationDataClass()).data,
        )
