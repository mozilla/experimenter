import datetime

from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusExperimentCsvSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


class TestNimbusExperimentCsvSerializer(TestCase):
    maxDiff = None

    def test_serializer_outputs_expected_schema_with_results_link(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=application,
            feature_configs=[feature_config],
            start_date=datetime.date(2019, 5, 1),
            end_date=datetime.date(2019, 5, 2),
        )

        serializer = NimbusExperimentCsvSerializer(experiment)
        self.assertDictEqual(
            serializer.data,
            {
                "launch_month": experiment.launch_month,
                "product_area": experiment.application,
                "experiment_name": experiment.name,
                "owner": experiment.owner.email,
                "feature_configs": feature_config.name,
                "_start_date": "2019-05-01",
                "enrollment_duration": experiment.enrollment_duration,
                "_end_date": "2019-05-02",
                "results_url": f"{experiment.experiment_url}results",
                "experiment_summary": experiment.experiment_url,
                "rollout": experiment.is_rollout,
                "hypothesis": experiment.hypothesis,
                "takeaways_metric_gain": experiment.takeaways_metric_gain,
                "takeaways_gain_amount": experiment.takeaways_gain_amount,
                "takeaways_qbr_learning": experiment.takeaways_qbr_learning,
                "takeaways_summary": experiment.takeaways_summary,
            },
        )
