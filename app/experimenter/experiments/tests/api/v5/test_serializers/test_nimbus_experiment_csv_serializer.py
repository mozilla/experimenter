from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusExperimentCSVSerializer
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.tests.factories.nimbus import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


class TestNimbusExperiment_Csv_Serializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        application = NimbusConstants.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)

        experiment = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config]
        )
        serializer = NimbusExperimentCSVSerializer(experiment)
        self.assertDictEqual(
            serializer.data,
            {
                "launch_month": experiment.launch_month,
                "product_area": experiment.application.value,
                "experiment_name": experiment.name,
                "feature_configs": getattr(feature_config, "name"),
                "owner": experiment.owner.email,
                "start_date": experiment.start_date,
                "enrollment_duration": experiment.enrollment_duration,
                "end_date": experiment.end_date,
                "monitoring_dashboard_url": experiment.monitoring_dashboard_url,
                "rollout": experiment.is_rollout,
                "hypothesis": experiment.hypothesis,
            },
        )
