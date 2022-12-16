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
        # ???
        # this should not be valid because:
        # is_locked->True (preview) and is_modifying_locked_fields=True
        self.assertTrue(serializer.is_valid())
        import ipdb
        ipdb.set_trace()
        self.assertIn("experiment", serializer.errors)

    def test_unable_to_update_experiment_in_publish_status(self):
        experiment = NimbusExperimentFactory.create(
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
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
        # this is valid because
        # is_locked->False (draft) and is_modifying_locked_fields=True
        # False and True = False
        self.assertTrue(serializer.is_valid())
        # import ipdb
        # ipdb.set_trace()
        # self.assertIn("experiment", serializer.errors)

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
    def test_update_experiment_publish_status_errors_for_status_complete(
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
        # import ipdb
        # ipdb.set_trace()
        # self.assertEquals(serializer.is_valid(), valid)

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
    def test_update_rollout_publish_status_errors_for_status_complete(
        self, publish_status, valid
    ):
        """ We do not prevent a rollout from being Status.COMPLETE """

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
        # import ipdb
        # ipdb.set_trace()
        # self.assertEquals(serializer.is_valid(), valid)

    @parameterized.expand(
        [
            [
                NimbusExperiment.PublishStatus.IDLE,
                True,
            ],
            [ 
                # Our serializer doesn't prevent an experiment from being dirty.
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
    def test_update_experiment_publish_status_errors_for_status_live(self, publish_status, valid):
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

    @parameterized.expand(
        [
            [ # why wasn't changelog popped? added to exempt list :/
                NimbusExperiment.PublishStatus.IDLE, # cannot modify changelog? 
                True,
            ],
            [
                NimbusExperiment.PublishStatus.DIRTY,
                True,
            ],
            [ # if publish_status is moving from IDLE -> REVIEW
              # that would denote ending the rollout
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
    def test_update_rollout_publish_status_errors_for_status_live(self, publish_status, valid):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            is_rollout=True
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

    @parameterized.expand(
        [
            [
                # Should we be allowed to edit allowed fields in experiments
                # when we're in a locked status? 
                NimbusExperiment.PublishStatus.IDLE,
                True,
            ],
            [
                # Our serializer doesn't prevent an experiment from being dirty.
                NimbusExperiment.PublishStatus.DIRTY,
                True,
            ],
            [
                # same here - we're locked?
                NimbusExperiment.PublishStatus.REVIEW,
                True,
            ],
            [
                # same here - we're locked?
                NimbusExperiment.PublishStatus.APPROVED,
                True,
            ],
            [
                NimbusExperiment.PublishStatus.WAITING,
                False,
            ],
        ]
    )
    def test_update_experiment_publish_status_errors_for_status_preview(self, publish_status, valid):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.PREVIEW,
            is_rollout=False,
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

    @parameterized.expand(
        [
            # [
            #     NimbusExperiment.PublishStatus.IDLE,
            #     False,
            # ],
            # [
            #     NimbusExperiment.PublishStatus.DIRTY,
            #     False,
            # ],
            # [
            #     # We are totally locking down editing (even allowed)
            #     # fields when it is in a non-editable status for rollouts.
            #     # Is this right?
            #     NimbusExperiment.PublishStatus.REVIEW,
            #     False,
            # ],
            # [
            #     NimbusExperiment.PublishStatus.APPROVED,
            #     False,
            # ],
            [
                NimbusExperiment.PublishStatus.WAITING,
                False,
            ],
        ]
    )
    def test_update_rollout_publish_status_errors_for_status_preview(self, publish_status, valid):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.PREVIEW,
            is_rollout=True,
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
    def test_update_experiment_publish_status_errors_for_status_draft(self, publish_status, valid):
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
        # import ipdb
        # ipdb.set_trace()

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
    def test_update_rollout_publish_status_errors_for_status_draft(self, publish_status, valid):
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
        # import ipdb
        # ipdb.set_trace()