import datetime

from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusExperimentCsvSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusChangeLogFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.openidc.tests.factories import UserFactory


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
                "conclusion_recommendations": "",
                "project_impact": None,
                "next_steps": None,
                "reviewer_emails": experiment.owner.email,
                "editor_emails": experiment.owner.email,
                "analysis_errors_count": 0,
            },
        )

    def test_serializer_outputs_reviewers_editors_errors_and_takeaways(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=application,
            feature_configs=[feature_config],
            owner=UserFactory.create(email="owner@example.com"),
            conclusion_recommendations=[
                NimbusExperiment.ConclusionRecommendation.RERUN,
                NimbusExperiment.ConclusionRecommendation.GRADUATE,
            ],
            project_impact=NimbusExperiment.ProjectImpact.HIGH,
            next_steps="Ship it.",
            results_data={
                "v3": {
                    "errors": {
                        "ad_clicks": [
                            {"analysis_basis": "enrollments", "segment": "all"},
                            {"analysis_basis": "exposures", "segment": "all"},
                        ],
                        "experiment": [{"analysis_basis": "enrollments"}],
                    },
                }
            },
        )
        NimbusChangeLogFactory.create(
            experiment=experiment,
            changed_by=UserFactory.create(email="reviewer@example.com"),
            old_publish_status=NimbusExperiment.PublishStatus.REVIEW,
            new_publish_status=NimbusExperiment.PublishStatus.APPROVED,
        )
        NimbusChangeLogFactory.create(
            experiment=experiment,
            changed_by=UserFactory.create(email="editor@example.com"),
            old_publish_status=NimbusExperiment.PublishStatus.IDLE,
            new_publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

        data = NimbusExperimentCsvSerializer(experiment).data

        self.assertEqual(
            data["reviewer_emails"], "owner@example.com,reviewer@example.com"
        )
        self.assertEqual(
            data["editor_emails"],
            "editor@example.com,owner@example.com,reviewer@example.com",
        )
        self.assertEqual(data["analysis_errors_count"], 3)
        self.assertEqual(data["conclusion_recommendations"], "Rerun,Graduate")
        self.assertEqual(data["project_impact"], NimbusExperiment.ProjectImpact.HIGH)
        self.assertEqual(data["next_steps"], "Ship it.")
