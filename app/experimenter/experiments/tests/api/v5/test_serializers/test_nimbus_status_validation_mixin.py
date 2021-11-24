from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusStatusValidationMixin(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_update_experiment_publish_status_while_in_preview(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.APPROVED,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    def test_update_experiment_with_invalid_status_error(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "public_description": "who knows, really",
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("experiment", serializer.errors)

    def test_update_experiment_with_invalid_publish_status_error(self):
        experiment = NimbusExperimentFactory.create(
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "public_description": "who knows, really",
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("experiment", serializer.errors)
