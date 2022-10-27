from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory
from parameterized import parameterized


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
        self.assertFalse(serializer.is_valid())
        self.assertIn("publish_status", serializer.errors)

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

    def test_unable_to_update_experiment_in_publish_status(self):
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

    @parameterized.expand(
        [
            [NimbusExperimentFactory.Lifecycles.CREATED, NimbusExperiment.PublishStatus.IDLE, True],
            [NimbusExperimentFactory.Lifecycles.CREATED, NimbusExperiment.PublishStatus.DIRTY, True],
            [NimbusExperimentFactory.Lifecycles.CREATED, NimbusExperiment.PublishStatus.REVIEW, True],
            [NimbusExperimentFactory.Lifecycles.CREATED, NimbusExperiment.PublishStatus.APPROVED, False],
            [NimbusExperimentFactory.Lifecycles.CREATED, NimbusExperiment.PublishStatus.WAITING, False],
        ]
    )    
    def test_update_publish_status_errors_for_create(self, lifecycle, status, valid):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)
    
    @parameterized.expand(
        [
            [NimbusExperimentFactory.Lifecycles.PREVIEW, NimbusExperiment.PublishStatus.IDLE, True],
            [NimbusExperimentFactory.Lifecycles.PREVIEW, NimbusExperiment.PublishStatus.DIRTY, True], # should this be False? 
            [NimbusExperimentFactory.Lifecycles.PREVIEW, NimbusExperiment.PublishStatus.REVIEW, True],
            [NimbusExperimentFactory.Lifecycles.PREVIEW, NimbusExperiment.PublishStatus.APPROVED, False],
            [NimbusExperimentFactory.Lifecycles.PREVIEW, NimbusExperiment.PublishStatus.WAITING, False],
        ]
    )    
    def test_update_publish_status_errors_for_preview(self, lifecycle, status, valid):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)

    @parameterized.expand(
        [
            [NimbusExperimentFactory.Lifecycles.LIVE_IDLE, NimbusExperiment.PublishStatus.IDLE, True],
            [NimbusExperimentFactory.Lifecycles.LIVE_IDLE, NimbusExperiment.PublishStatus.DIRTY, True],
            [NimbusExperimentFactory.Lifecycles.LIVE_IDLE, NimbusExperiment.PublishStatus.REVIEW, True],
            [NimbusExperimentFactory.Lifecycles.LIVE_IDLE, NimbusExperiment.PublishStatus.APPROVED, False],
            [NimbusExperimentFactory.Lifecycles.LIVE_IDLE, NimbusExperiment.PublishStatus.WAITING, False],
        ]
    )    
    def test_update_publish_status_errors_for_live_idle(self, lifecycle, status, valid):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)

    @parameterized.expand(
        [
            [NimbusExperimentFactory.Lifecycles.LIVE_DIRTY, NimbusExperiment.PublishStatus.IDLE, False],
            [NimbusExperimentFactory.Lifecycles.LIVE_DIRTY, NimbusExperiment.PublishStatus.DIRTY, True],
            [NimbusExperimentFactory.Lifecycles.LIVE_DIRTY, NimbusExperiment.PublishStatus.REVIEW, True],
            [NimbusExperimentFactory.Lifecycles.LIVE_DIRTY, NimbusExperiment.PublishStatus.APPROVED, False],
            [NimbusExperimentFactory.Lifecycles.LIVE_DIRTY, NimbusExperiment.PublishStatus.WAITING, False],
        ]
    )    
    def test_update_publish_status_errors_for_live_dirty(self, lifecycle, status, valid):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
        )
        serializer = NimbusExperimentSerializer(
            experiment,
            data={
                "publish_status": status,
                "changelog_message": "test changelog message",
            },
            context={"user": self.user},
        )
        self.assertEquals(serializer.is_valid(), valid)

    
    # @parameterized.expand(
    #     [
            # [NimbusExperimentFactory.Lifecycles.CREATED, NimbusExperiment.PublishStatus.IDLE],
    #         [NimbusExperimentFactory.Lifecycles.CREATED, NimbusExperiment.PublishStatus.DIRTY],
    #         [NimbusExperimentFactory.Lifecycles.CREATED, NimbusExperiment.PublishStatus.REVIEW],
    #         [NimbusExperimentFactory.Lifecycles.CREATED, NimbusExperiment.PublishStatus.APPROVED],
    #         [NimbusExperimentFactory.Lifecycles.CREATED, NimbusExperiment.PublishStatus.WAITING],
    #         [NimbusExperimentFactory.Lifecycles.PREVIEW],
    #         [NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE],
    #         [NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE],
    #         [NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED],
    #         [NimbusExperimentFactory.Lifecycles.LAUNCH_REJECT],
    #         [NimbusExperimentFactory.Lifecycles.LIVE_IDLE],
    #         [NimbusExperimentFactory.Lifecycles.LIVE_DIRTY],
    #         [NimbusExperimentFactory.Lifecycles.LIVE_REVIEW_REQUESTED],
    #         [NimbusExperimentFactory.Lifecycles.LIVE_REVIEW_APPROVED],
    #         [NimbusExperimentFactory.Lifecycles.LIVE_REVIEW_WAITING],
    #     ]
    # )    
    # def test_upd(self, lifecycle, publishStatus):
    #     experiment = NimbusExperimentFactory.create(
    #         lifecycle=lifecycle,
    #         publish_status=lifecycle,
    #     )
    #     serializer = NimbusExperimentSerializer(
    #         experiment,
    #         data={
    #             "publish_status": NimbusExperiment.PublishStatus.APPROVED,
    #             "changelog_message": "test changelog message",
    #         },
    #         context={"user": self.user},
    #     )
    #     self.assertFalse(serializer.is_valid())
    #     self.assertIn("experiment", serializer.errors)
