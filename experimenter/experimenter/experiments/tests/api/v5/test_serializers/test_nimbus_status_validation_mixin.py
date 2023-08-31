from django.test import TestCase
from parameterized import parameterized

from experimenter.experiments.api.v5.serializers import (
    NimbusExperimentSerializer,
    TransitionConstants,
)
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

    @parameterized.expand(
        [
            ["public_description", NimbusExperiment.Status.PREVIEW, False, False, False],
            ["public_description", NimbusExperiment.Status.DRAFT, False, True, True],
            ["takeaways_summary", NimbusExperiment.Status.DRAFT, True, True, True],
        ]
    )
    def test_locked_fields_and_status_errors(
        self, field_to_change, status, field_valid, status_valid, serializer_valid
    ):
        fields = (
            TransitionConstants.STATUS_UPDATE_EXEMPT_FIELDS["all"]
            + TransitionConstants.STATUS_UPDATE_EXEMPT_FIELDS["experiments"]
        )
        status_allowed = (
            TransitionConstants.STATUS_ALLOWS_UPDATE["all"]
            + TransitionConstants.STATUS_ALLOWS_UPDATE["experiments"]
        )

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

        self.assertEqual(field_to_change in fields, field_valid)
        self.assertEqual(status in status_allowed, status_valid)
        self.assertEqual(serializer.is_valid(), serializer_valid)

    @parameterized.expand(
        [
            [
                NimbusExperiment.PublishStatus.IDLE,
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
        self.assertEqual(serializer.is_valid(), valid)

    @parameterized.expand(
        [
            [
                NimbusExperiment.PublishStatus.IDLE,
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
        self.assertEqual(serializer.is_valid(), valid)

    @parameterized.expand(
        [
            [
                NimbusExperiment.PublishStatus.IDLE,
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
        self.assertEqual(serializer.is_valid(), valid)

    @parameterized.expand(
        [
            [
                NimbusExperiment.PublishStatus.IDLE,
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
        self.assertEqual(serializer.is_valid(), valid)
