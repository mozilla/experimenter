from django.test import TestCase

from experimenter.base.models import SiteFlag, SiteFlagNameChoices
from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusStatusTransitionValidator(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_update_experiment_status_error(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.LIVE,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["status"][0],
            "Nimbus Experiment status cannot transition from Draft to Live.",
        )

    def test_update_publish_status_from_approved_to_review_error(self):
        experiment = NimbusExperimentFactory.create(
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["publish_status"][0],
            "Nimbus Experiment publish_status cannot transition from Approved to Review.",
        )

    def test_launch_request_while_disabled_error(self):
        SiteFlag(name=SiteFlagNameChoices.LAUNCHING_DISABLED.name, value=True).save()
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.DRAFT,
                "status_next": NimbusExperiment.Status.LIVE,
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "changelog_message": "Review Requested for Launch",
            },
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["status_next"][0],
            NimbusExperiment.ERROR_LAUNCHING_DISABLED,
        )
