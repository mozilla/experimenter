from django.test import TestCase
from parameterized import parameterized

from experimenter.base.models import SiteFlag, SiteFlagNameChoices
from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusStatusNextTransitionValidator(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_launch_request_while_disabled_error(self):
        SiteFlag(name=SiteFlagNameChoices.LAUNCHING_DISABLED.name, value=True).save()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
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
                True,
            ],
            [
                NimbusExperiment.Status.COMPLETE,
                False,
            ],
        ]
    )
    def test_update_status_errors_for_status_next_live(
        self, status, valid
    ):
        experiment = NimbusExperimentFactory.create(
            status=status
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status_next": NimbusExperiment.Status.LIVE,
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
    def test_update_status_errors_for_status_next_complete(
        self, status, valid
    ):
        experiment = NimbusExperimentFactory.create(
            status=status
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status_next": NimbusExperiment.Status.COMPLETE,
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
                False,
            ],
        ]
    )
    def test_update_status_errors_for_status_next_draft(
        self, status, valid
    ):
        experiment = NimbusExperimentFactory.create(
            status=status
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status_next": NimbusExperiment.Status.DRAFT,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)

    def test_allow_live_experiment_to_be_complete(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_rollout=False,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.LIVE,
                "publish_status": NimbusExperiment.PublishStatus.REVIEW,
                "status_next": NimbusExperiment.Status.COMPLETE,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    def test_allow_live_experiment_to_be_dirty(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_rollout=False,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.LIVE,
                "publish_status": NimbusExperiment.PublishStatus.DIRTY,
                "status_next": NimbusExperiment.Status.LIVE,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    def test_allow_live_rollout_to_be_dirty(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_rollout=True,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "status": NimbusExperiment.Status.LIVE,
                "publish_status": NimbusExperiment.PublishStatus.DIRTY,
                "status_next": NimbusExperiment.Status.LIVE,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())