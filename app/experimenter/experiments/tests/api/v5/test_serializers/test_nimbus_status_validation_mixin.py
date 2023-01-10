from django.test import TestCase
from parameterized import parameterized

from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusStatusValidationMixin(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_update_experiment_with_invalid_status_error(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW,
            is_rollout=False,
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

    def test_update_rollout_with_invalid_status_error(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW,
            is_rollout=True,
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

    def test_locked_fields_and_status_error(self):
        fields = (
            NimbusExperiment.STATUS_UPDATE_EXEMPT_FIELDS["all"]
            + NimbusExperiment.STATUS_UPDATE_EXEMPT_FIELDS["experiments"]
        )
        status_allowed = (
            NimbusExperiment.STATUS_ALLOWS_UPDATE["all"]
            + NimbusExperiment.STATUS_ALLOWS_UPDATE["experiments"]
        )

        field_to_change = "public_description"
        status = NimbusExperiment.Status.PREVIEW

        experiment = NimbusExperimentFactory.create(
            status=status,
            is_rollout=True,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                field_to_change: "who knows, really",
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )

        self.assertFalse(field_to_change in fields)
        self.assertFalse(status in status_allowed)

        self.assertFalse(serializer.is_valid())
        self.assertIn("experiment", serializer.errors)

    def test_locked_fields_and_valid_status_does_not_error(self):
        fields = (
            NimbusExperiment.STATUS_UPDATE_EXEMPT_FIELDS["all"]
            + NimbusExperiment.STATUS_UPDATE_EXEMPT_FIELDS["experiments"]
        )
        status_allowed = (
            NimbusExperiment.STATUS_ALLOWS_UPDATE["all"]
            + NimbusExperiment.STATUS_ALLOWS_UPDATE["experiments"]
        )

        field_to_change = "public_description"
        status = NimbusExperiment.Status.DRAFT

        experiment = NimbusExperimentFactory.create(
            status=status,
            is_rollout=True,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                field_to_change: "who knows, really",
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )

        self.assertFalse(field_to_change in fields)
        self.assertTrue(status in status_allowed)
        self.assertTrue(serializer.is_valid())

    def test_unlocked_fields_and_valid_status_does_not_error(self):
        fields = (
            NimbusExperiment.STATUS_UPDATE_EXEMPT_FIELDS["all"]
            + NimbusExperiment.STATUS_UPDATE_EXEMPT_FIELDS["experiments"]
        )
        status_allowed = (
            NimbusExperiment.STATUS_ALLOWS_UPDATE["all"]
            + NimbusExperiment.STATUS_ALLOWS_UPDATE["experiments"]
        )

        field_to_change = "takeaways_summary"
        status = NimbusExperiment.Status.DRAFT

        experiment = NimbusExperimentFactory.create(
            status=status,
            is_rollout=True,
        )

        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                field_to_change: "who knows, really",
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )

        self.assertTrue(field_to_change in fields)
        self.assertTrue(status in status_allowed)
        self.assertTrue(serializer.is_valid())

    @parameterized.expand(
        [
            [
                NimbusExperiment.PublishStatus.IDLE,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.DIRTY,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.REVIEW,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.APPROVED,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.WAITING,
                False,
            ],
        ]
    )
    def test_update_publish_status_errors_for_status_complete(
        self, publish_status, valid
    ):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.COMPLETE
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": publish_status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)

    @parameterized.expand(
        [
            [
                NimbusExperiment.PublishStatus.IDLE,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.DIRTY,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.REVIEW,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.APPROVED,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.WAITING,
                False,
            ],
        ]
    )
    def test_update_publish_status_errors_for_status_live(self, publish_status, valid):
        experiment = NimbusExperimentFactory.create(status=NimbusExperiment.Status.LIVE)
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": publish_status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)

    @parameterized.expand(
        [
            [
                NimbusExperiment.PublishStatus.IDLE,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.DIRTY,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.REVIEW,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.APPROVED,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.WAITING,
                False,
            ],
        ]
    )
    def test_update_publish_status_errors_for_status_preview(self, publish_status, valid):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": publish_status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)

    @parameterized.expand(
        [
            [
                NimbusExperiment.PublishStatus.IDLE,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.DIRTY,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.REVIEW,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.APPROVED,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.WAITING,
                False,
            ],
        ]
    )
    def test_update_publish_status_errors_for_status_draft(self, publish_status, valid):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": publish_status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)
