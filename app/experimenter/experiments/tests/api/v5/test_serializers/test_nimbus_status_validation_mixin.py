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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.PREVIEW,
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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
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
            # [
            #     NimbusExperiment.PublishStatus.IDLE,
            #     True,
            # ],
            [
                NimbusExperiment.PublishStatus.DIRTY,
                True,
            ],
    #         [
    #             NimbusExperiment.PublishStatus.REVIEW,
    #             False,
    #         ],
    #         [
    #             NimbusExperiment.PublishStatus.APPROVED,
    #             False,
    #         ],
    #         [
    #             NimbusExperiment.PublishStatus.WAITING,
    #             False,
    #         ],
        ]
    )
    def test_update_publish_status_errors_for_status_live_non_rollout(self, publish_status, valid):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            is_rollout=False
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
        # import ipdb
        # ipdb.set_trace()
        # self.assertEquals(serializer.is_valid(), valid)

    # def test_update_publish_status_for_status_live_to_complete(self):
    #     experiment = NimbusExperimentFactory.create_with_lifecycle(
    #         lifecycle=NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
    #         is_rollout=False
    #     )
    #     serializer = NimbusExperimentSerializer(
    #         experiment,
    #         data={
    #             "publish_status": NimbusExperiment.PublishStatus.REVIEW,
    #             "status_next": NimbusExperiment.Status.COMPLETE,
    #             "changelog_message": "test changelog message",
    #         },
    #         context={"user": self.user},
    #     )
    #     self.assertEquals(serializer.is_valid(), False)
    #     # # self.assertTrue(serializer.is_valid())
    #     # import ipdb
    #     # ipdb.set_trace()
    #     # self.assertEquals(serializer.is_valid(), False)

    # @parameterized.expand(
    #     [
    #         [
    #             NimbusExperiment.PublishStatus.IDLE,
    #             True,
    #         ],
    #         [
    #             NimbusExperiment.PublishStatus.DIRTY,
    #             True,
    #         ],
    #         [
    #             NimbusExperiment.PublishStatus.REVIEW,
    #             True,
    #         ],
    #         [
    #             NimbusExperiment.PublishStatus.APPROVED,
    #             True,
    #         ],
    #         [
    #             NimbusExperiment.PublishStatus.WAITING,
    #             False,
    #         ],
    #     ]
    # )
    # def test_update_publish_status_errors_for_status_live_rollouts(self, publish_status, valid):
    #     experiment = NimbusExperimentFactory.create_with_lifecycle(
    #         lifecycle=NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
    #         is_rollout=True
    #     )
    #     serializer = NimbusExperimentSerializer(
    #         experiment,
    #         data={
    #             "publish_status": publish_status,
    #             "changelog_message": "test changelog message",
    #         },
    #         context={"user": self.user},
    #     )
    #     self.assertEquals(serializer.is_valid(), valid)

    # @parameterized.expand(
    #     [
    #         # [
    #         #     NimbusExperiment.PublishStatus.IDLE,
    #         #     False,
    #         # ],
    #         # [
    #         #     NimbusExperiment.PublishStatus.DIRTY,
    #         #     False,
    #         # ],
    #         [
    #             NimbusExperiment.PublishStatus.REVIEW,
    #             True,
    #         ],
    #         # [
    #         #     NimbusExperiment.PublishStatus.APPROVED,
    #         #     True,
    #         # ],
    #         # [
    #         #     NimbusExperiment.PublishStatus.WAITING,
    #         #     False,
    #         # ],
    #     ]
    # )
    # def test_update_publish_status_errors_for_status_preview(self, publish_status, valid):
    #     experiment = NimbusExperimentFactory.create_with_lifecycle(
    #         lifecycle=NimbusExperimentFactory.Lifecycles.PREVIEW
    #     )
    #     serializer = NimbusExperimentSerializer(
    #         experiment,
    #         data={
    #             "publish_status": publish_status,
    #             "changelog_message": "test changelog message",
    #         },
    #         context={"user": self.user},
    #     )
    #     self.assertEquals(serializer.is_valid(), valid)
        # import ipdb
        # ipdb.set_trace()
        # self.assertEquals(serializer.is_valid(), valid)

    # @parameterized.expand(
    #     [
    #         [
    #             NimbusExperiment.PublishStatus.IDLE,
    #             True,
    #         ],
    #         [
    #             NimbusExperiment.PublishStatus.DIRTY,
    #             True,
    #         ],
    #         [
    #             NimbusExperiment.PublishStatus.REVIEW,
    #             True,
    #         ],
    #         [
    #             NimbusExperiment.PublishStatus.APPROVED,
    #             True,
    #         ],
    #         [
    #             NimbusExperiment.PublishStatus.WAITING,
    #             False,
    #         ],
    #     ]
    # )
    # def test_update_publish_status_errors_for_status_draft(self, publish_status, valid):
    #     experiment = NimbusExperimentFactory.create(
    #         status=NimbusExperiment.Status.DRAFT,
    #     )
    #     serializer = NimbusExperimentSerializer(
    #         experiment,
    #         data={
    #             "publish_status": publish_status,
    #             "changelog_message": "test changelog message",
    #         },
    #         context={"user": self.user},
    #     )
    #     self.assertEquals(serializer.is_valid(), valid)
