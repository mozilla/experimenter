import datetime

from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusExperimentCsvSerializer
from experimenter.experiments.constants.nimbus import NimbusConstants
from experimenter.experiments.models.nimbus import NimbusExperiment
from experimenter.experiments.tests.factories.nimbus import (
    NimbusChangeLogFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


class TestNimbusExperimentCsvSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        application = NimbusConstants.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)

        experiment = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config]
        )
        NimbusChangeLogFactory.create(
            experiment=experiment,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
            changed_on=datetime.date(2019, 5, 1),
        )
        serializer = NimbusExperimentCsvSerializer(experiment)
        self.assertDictEqual(
            serializer.data,
            {
                "launch_month": experiment.launch_month,
                "product_area": experiment.application.value,
                "experiment_name": experiment.name,
                "owner": experiment.owner.email,
                "feature_configs": getattr(feature_config, "name"),
                "start_date": experiment.start_date,
                "enrollment_duration": experiment.enrollment_duration,
                "end_date": experiment.end_date,
                "monitoring_dashboard_url": experiment.monitoring_dashboard_url,
                "rollout": experiment.is_rollout,
                "hypothesis": experiment.hypothesis,
            },
        )
