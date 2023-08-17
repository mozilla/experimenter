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
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.jetstream.tests.mixins import MockSizingDataMixin


class TestNimbusExperimentCsvListView(TestCase):
    def test_get_returns_csv_info_sorted_by_start_date(self):
        user_email = "user@example.com"
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment_1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date(2022, 5, 1),
            name="Experiment 1",
            application=application,
            feature_configs=[feature_config],
        )

        experiment_2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date(2020, 5, 1),
            name="Experiment 2",
            application=application,
            feature_configs=[feature_config],
        )

        experiment_3 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date(2019, 5, 1),
            name="Experiment 3",
            application=application,
            feature_configs=[feature_config],
        )

        experiment_4 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date(2021, 5, 1),
            name="Experiment 4",
            application=application,
            feature_configs=[feature_config],
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

    def test_get_returns_csv_filter_archived_experiments_info(self):
        user_email = "user@example.com"
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment_1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            start_date=datetime.date(2019, 5, 1),
            application=application,
            feature_configs=[feature_config],
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


class TestNimbusConfigurationView(MockSizingDataMixin, TestCase):
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
