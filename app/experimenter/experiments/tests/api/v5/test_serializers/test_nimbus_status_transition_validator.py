from django.test import TestCase
from parameterized import parameterized

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

    def test_end_enrolment_request_while_disabled_error(self):
        SiteFlag(name=SiteFlagNameChoices.LAUNCHING_DISABLED.name, value=True).save()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.LIVE,
                "status_next": NimbusExperiment.Status.LIVE,
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "changelog_message": "Review Requested for Launch",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    def test_end_experiment_request_while_disabled_error(self):
        SiteFlag(name=SiteFlagNameChoices.LAUNCHING_DISABLED.name, value=True).save()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_PAUSED
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.LIVE,
                "status_next": NimbusExperiment.Status.COMPLETE,
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "changelog_message": "Review Requested for Launch",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    @parameterized.expand(
        [
            [
                NimbusExperiment.Status.DRAFT,
                True,
            ],
            [
                NimbusExperiment.Status.PREVIEW,
                True,
            ],
            [
                NimbusExperiment.Status.LIVE,
                False,
            ],
            [
                NimbusExperiment.Status.COMPLETE,
                False,
            ],
        ]
    )
    def test_update_status_errors_for_status_draft(
        self, new_status, valid
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.CREATED
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": new_status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)

    @parameterized.expand(
        [
            [
                NimbusExperiment.Status.DRAFT,
                True,
            ],
            [
                NimbusExperiment.Status.PREVIEW,
                True,
            ],
            [
                NimbusExperiment.Status.LIVE,
                False,
            ],
            [
                NimbusExperiment.Status.COMPLETE,
                False,
            ],
        ]
    )
    def test_update_status_errors_for_status_preview(
        self, new_status, valid
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.PREVIEW
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": new_status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)

    @parameterized.expand(
        [
            [
                NimbusExperiment.Status.DRAFT,
                False,
            ],
            [
                NimbusExperiment.Status.PREVIEW,
                False,
            ],
            [
                NimbusExperiment.Status.LIVE,
                True,
            ],
            [
                NimbusExperiment.Status.COMPLETE,
                False,
            ],
        ]
    )
    def test_update_status_errors_for_status_live(
        self, new_status, valid
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": new_status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)

    @parameterized.expand(
        [
            [
                NimbusExperiment.Status.DRAFT,
                False,
            ],
            [
                NimbusExperiment.Status.PREVIEW,
                False,
            ],
            [
                NimbusExperiment.Status.LIVE,
                False,
            ],
            [
                NimbusExperiment.Status.COMPLETE,
                True,
            ],
        ]
    )
    def test_update_status_errors_for_status_complete(
        self, new_status, valid
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": new_status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)
