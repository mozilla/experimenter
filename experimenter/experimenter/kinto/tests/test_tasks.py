from unittest import mock

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from parameterized import parameterized

from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import (
    NimbusChangeLog,
    NimbusEmail,
    NimbusExperiment,
)
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.kinto import tasks
from experimenter.kinto.client import KINTO_REVIEW_STATUS, KINTO_ROLLBACK_STATUS
from experimenter.kinto.tests.mixins import MockKintoClientMixin


class TestNimbusCheckKintoPushQueue(MockKintoClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        mock_dispatchee_task_patcher = mock.patch(
            "experimenter.kinto.tasks.nimbus_check_kinto_push_queue_by_collection.delay"
        )
        self.mock_dispatchee_task = mock_dispatchee_task_patcher.start()
        self.addCleanup(mock_dispatchee_task_patcher.stop)

    def test_dispatches_check_push_queue(self):
        tasks.nimbus_check_kinto_push_queue()
        for collection in (
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            settings.KINTO_COLLECTION_NIMBUS_MOBILE,
            settings.KINTO_COLLECTION_NIMBUS_WEB,
        ):
            self.mock_dispatchee_task.assert_any_call(collection)


class TestNimbusCheckKintoPushQueueByCollection(MockKintoClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        mock_push_task_patcher = mock.patch(
            "experimenter.kinto.tasks.nimbus_push_experiment_to_kinto.delay"
        )
        self.mock_push_task = mock_push_task_patcher.start()
        self.addCleanup(mock_push_task_patcher.stop)

        mock_update_task_patcher = mock.patch(
            "experimenter.kinto.tasks.nimbus_update_experiment_in_kinto.delay"
        )
        self.mock_update_task = mock_update_task_patcher.start()
        self.addCleanup(mock_update_task_patcher.stop)

        mock_end_task_patcher = mock.patch(
            "experimenter.kinto.tasks.nimbus_end_experiment_in_kinto.delay"
        )
        self.mock_end_task = mock_end_task_patcher.start()
        self.addCleanup(mock_end_task_patcher.stop)

    def test_check_with_empty_queue_pushes_nothing(self):
        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_kinto_client.patch_collection.assert_not_called()
        self.mock_push_task.assert_not_called()
        self.mock_update_task.assert_not_called()
        self.mock_end_task.assert_not_called()

    def test_check_with_no_approved_publish_status_pushes_nothing(self):
        for lifecycle in [
            NimbusExperimentFactory.Lifecycles.CREATED,
            NimbusExperimentFactory.Lifecycles.LAUNCH_REVIEW_REQUESTED,
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            NimbusExperimentFactory.Lifecycles.PAUSING_REVIEW_REQUESTED,
            NimbusExperimentFactory.Lifecycles.ENDING_REVIEW_REQUESTED,
        ]:
            NimbusExperimentFactory.create_with_lifecycle(
                lifecycle,
                application=NimbusExperiment.Application.DESKTOP,
            )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )
        self.mock_kinto_client.patch_collection.assert_not_called()
        self.mock_push_task.assert_not_called()
        self.mock_update_task.assert_not_called()
        self.mock_end_task.assert_not_called()

    @parameterized.expand(
        [
            [
                NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            ],
            [
                NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            ],
            [
                NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            ],
        ]
    )
    @override_settings(KINTO_REVIEW_TIMEOUT=60)
    def test_check_with_pending_review_before_timeout_aborts_early(self, lifecycle):
        NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=lifecycle,
            application=NimbusExperiment.Application.DESKTOP,
            with_latest_change_now=True,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )
        self.mock_kinto_client.patch_collection.assert_not_called()
        self.mock_push_task.assert_not_called()
        self.mock_update_task.assert_not_called()
        self.mock_end_task.assert_not_called()

    def test_check_with_approved_launch_and_no_kinto_pending_pushes_experiment(
        self,
    ):
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )
        self.mock_push_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_experiment.id
        )

    def test_check_with_approved_update_and_no_kinto_pending_updates_experiment(
        self,
    ):
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )
        self.mock_update_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_experiment.id
        )

    def test_check_with_approved_end_and_no_kinto_pending_ends_experiment(self):
        ending_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )
        self.mock_end_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, ending_experiment.id
        )

    @override_settings(KINTO_REVIEW_TIMEOUT=0)
    def test_check_with_timeout_launch_review_and_queued_launch_rolls_back_and_pushes(
        self,
    ):
        pending_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=timezone.now(),
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_push_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_experiment.id
        )
        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            data={"status": "to-rollback"},
            bucket="main-workspace",
        )

        pending_experiment = NimbusExperiment.objects.get(id=pending_experiment.id)
        self.assertEqual(
            pending_experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW
        )
        self.assertIsNone(pending_experiment.published_date)
        self.assertTrue(
            pending_experiment.changes.filter(
                old_status=NimbusExperiment.Status.DRAFT,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.DRAFT,
                new_publish_status=NimbusExperiment.PublishStatus.REVIEW,
            ).exists()
        )

    @override_settings(KINTO_REVIEW_TIMEOUT=0)
    def test_check_with_timeout_update_review_and_queued_launch_rolls_back_and_pushes(
        self,
    ):
        expected_published_date = timezone.now()
        pending_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=expected_published_date,
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_push_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_experiment.id
        )
        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            data={"status": "to-rollback"},
            bucket="main-workspace",
        )

        pending_experiment = NimbusExperiment.objects.get(id=pending_experiment.id)
        self.assertEqual(
            pending_experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW
        )
        self.assertEqual(pending_experiment.published_date, expected_published_date)
        self.assertTrue(
            pending_experiment.changes.filter(
                old_status=NimbusExperiment.Status.LIVE,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.REVIEW,
            ).exists()
        )

    @override_settings(KINTO_REVIEW_TIMEOUT=0)
    def test_check_with_timeout_end_review_and_queued_launch_rolls_back_and_pushes(
        self,
    ):
        expected_published_date = timezone.now()
        pending_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=expected_published_date,
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_push_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_experiment.id
        )
        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            data={"status": "to-rollback"},
            bucket="main-workspace",
        )

        pending_experiment = NimbusExperiment.objects.get(id=pending_experiment.id)
        self.assertEqual(
            pending_experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW
        )
        self.assertEqual(pending_experiment.published_date, expected_published_date)
        self.assertTrue(
            pending_experiment.changes.filter(
                old_status=NimbusExperiment.Status.LIVE,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.REVIEW,
            ).exists()
        )

    def test_check_with_rejected_launch_rolls_back_and_pushes(self):
        rejected_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=timezone.now(),
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_rejected_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_push_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_experiment.id
        )
        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            data={"status": KINTO_ROLLBACK_STATUS},
        )

        rejected_experiment = NimbusExperiment.objects.get(id=rejected_experiment.id)
        self.assertEqual(rejected_experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(
            rejected_experiment.publish_status, NimbusExperiment.PublishStatus.IDLE
        )
        self.assertIsNone(rejected_experiment.status_next)
        self.assertIsNone(rejected_experiment.published_date)

        self.assertTrue(
            rejected_experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.DRAFT,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.DRAFT,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )

    def test_check_with_rejected_update_rolls_back_and_pushes(self):
        expected_published_date = timezone.now()
        rejected_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=expected_published_date,
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_rejected_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_push_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_experiment.id
        )
        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            data={"status": KINTO_ROLLBACK_STATUS},
        )

        rejected_experiment = NimbusExperiment.objects.get(id=rejected_experiment.id)
        self.assertEqual(rejected_experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(
            rejected_experiment.publish_status, NimbusExperiment.PublishStatus.IDLE
        )
        self.assertIsNone(rejected_experiment.status_next)
        self.assertFalse(rejected_experiment.is_paused)
        self.assertEqual(rejected_experiment.published_date, expected_published_date)

        self.assertTrue(
            rejected_experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )

    def test_check_with_rejected_update_live_rollout_rolls_back_and_pushes(self):
        expected_published_date = timezone.now()
        rejected_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
            is_rollout_dirty=True,
            published_date=expected_published_date,
        )
        self.setup_kinto_get_main_records([])
        self.setup_kinto_rejected_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            data={"status": KINTO_ROLLBACK_STATUS},
        )

        rejected_experiment = NimbusExperiment.objects.get(id=rejected_experiment.id)
        self.assertEqual(rejected_experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(
            rejected_experiment.publish_status, NimbusExperiment.PublishStatus.IDLE
        )
        self.assertTrue(rejected_experiment.is_rollout_dirty)
        self.assertIsNone(rejected_experiment.status_next)
        self.assertFalse(rejected_experiment.is_paused)
        self.assertEqual(rejected_experiment.published_date, expected_published_date)

        self.assertTrue(
            rejected_experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )

    def test_check_with_rejected_end_rolls_back_and_pushes(self):
        expected_published_date = timezone.now()
        rejected_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=expected_published_date,
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_rejected_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_push_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_experiment.id
        )
        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            data={"status": KINTO_ROLLBACK_STATUS},
        )

        rejected_experiment = NimbusExperiment.objects.get(id=rejected_experiment.id)
        self.assertEqual(rejected_experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(
            rejected_experiment.publish_status, NimbusExperiment.PublishStatus.IDLE
        )
        self.assertEqual(rejected_experiment.status_next, None)
        self.assertEqual(rejected_experiment.published_date, expected_published_date)

        self.assertTrue(
            rejected_experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )

    def test_check_with_rollout_rejected_end_rolls_back_and_pushes(self):
        expected_published_date = timezone.now()
        rejected_rollout = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
            published_date=expected_published_date,
        )
        launching_rollout = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_rejected_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_push_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_rollout.id
        )
        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            data={"status": KINTO_ROLLBACK_STATUS},
        )

        rejected_rollout = NimbusExperiment.objects.get(id=rejected_rollout.id)
        self.assertEqual(rejected_rollout.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(
            rejected_rollout.publish_status, NimbusExperiment.PublishStatus.IDLE
        )
        self.assertEqual(rejected_rollout.status_next, None)
        self.assertEqual(rejected_rollout.published_date, expected_published_date)

        self.assertTrue(
            rejected_rollout.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )

    def test_check_with_dirty_rollout_rejected_end_rolls_back_and_pushes(self):
        expected_published_date = timezone.now()
        rejected_rollout = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_DIRTY_ENDING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
            is_rollout_dirty=True,
            published_date=expected_published_date,
        )
        launching_rollout = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
        )

        # launch
        self.setup_kinto_get_main_records([])
        self.setup_kinto_rejected_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_push_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_rollout.id
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            data={"status": KINTO_ROLLBACK_STATUS},
        )

        # get rejected rollout
        rejected_rollout = NimbusExperiment.objects.get(id=rejected_rollout.id)
        self.assertEqual(rejected_rollout.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(
            rejected_rollout.publish_status, NimbusExperiment.PublishStatus.IDLE
        )
        self.assertEqual(rejected_rollout.status_next, None)
        self.assertTrue(rejected_rollout.is_rollout_dirty)
        self.assertEqual(rejected_rollout.published_date, expected_published_date)

        self.assertTrue(
            rejected_rollout.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )

    def test_check_with_approved_update_sets_experiment_to_idle_saves_published_dto(
        self,
    ):
        updated_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            slug="updated_experiment",
            published_dto={
                "id": "updated_experiment",
                "something": "else",
                "last_modified": "123",
            },
        )

        self.setup_kinto_get_main_records([updated_experiment.slug])
        self.setup_kinto_no_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        updated_experiment = NimbusExperiment.objects.get(id=updated_experiment.id)
        self.assertEqual(updated_experiment.status, NimbusExperiment.Status.LIVE)
        self.assertIsNone(updated_experiment.status_next)
        self.assertEqual(
            updated_experiment.publish_status, NimbusExperiment.PublishStatus.IDLE
        )
        self.assertEqual(
            updated_experiment.published_dto,
            {"id": updated_experiment.slug},
        )
        self.assertTrue(
            updated_experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )
        self.assertFalse(updated_experiment.is_rollout_dirty)

    def test_check_with_missing_review_and_queued_launch_rolls_back_and_pushes(self):
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_push_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_experiment.id
        )
        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            data={"status": "to-rollback"},
            bucket="main-workspace",
        )

    def test_check_with_missing_rejection_and_queued_launch_rolls_back_and_pushes(self):
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_rejected_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_push_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_experiment.id
        )
        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            data={"status": "to-rollback"},
            bucket="main-workspace",
        )

    def test_check_waiting_launching_experiment_with_signed_collection_becomes_rejection(
        self,
    ):
        waiting_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=timezone.now(),
        )

        self.setup_kinto_get_main_records([])
        self.setup_kinto_no_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        waiting_experiment = NimbusExperiment.objects.get(id=waiting_experiment.id)
        self.assertEqual(waiting_experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertIsNone(waiting_experiment.status_next)
        self.assertEqual(
            waiting_experiment.publish_status, NimbusExperiment.PublishStatus.IDLE
        )
        self.assertIsNone(waiting_experiment.published_date)
        self.assertTrue(
            waiting_experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.DRAFT,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.DRAFT,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
                message=NimbusChangeLog.Messages.REJECTED_FROM_KINTO,
            ).exists()
        )

    def test_launching_experiment_live_when_record_is_in_main(self):
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([launching_experiment.slug])
        self.setup_kinto_no_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        launching_experiment = NimbusExperiment.objects.get(id=launching_experiment.id)
        self.assertEqual(launching_experiment.status, NimbusExperiment.Status.LIVE)
        self.assertIsNone(launching_experiment.status_next)
        self.assertEqual(
            launching_experiment.publish_status, NimbusExperiment.PublishStatus.IDLE
        )
        self.assertEqual(
            launching_experiment.published_dto, {"id": launching_experiment.slug}
        )

        self.assertTrue(
            launching_experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.DRAFT,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )

    def test_ending_experiment_completed_when_record_is_not_in_main(self):
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_get_main_records([experiment1.slug])
        self.setup_kinto_no_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.assertTrue(
            experiment2.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.COMPLETE,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
                message=NimbusChangeLog.Messages.COMPLETED,
            ).exists()
        )

    def test_updating_experiment_with_published_dto_none_is_skipped(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_dto=None,
        )

        self.setup_kinto_get_main_records([experiment.slug])
        self.setup_kinto_no_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_kinto_client.patch_collection.assert_not_called()
        self.mock_push_task.assert_not_called()
        self.mock_update_task.assert_not_called()
        self.mock_end_task.assert_not_called()


class TestNimbusPushExperimentToKintoTask(MockKintoClientMixin, TestCase):
    def test_push_experiment_to_kinto(
        self,
    ):
        """Push desktop experiment to Kinto and validate its outgoing publish status,
        published_date, and changelogs"""
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=None,
        )

        tasks.nimbus_push_experiment_to_kinto(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
        )

        self.mock_kinto_client.create_record.assert_called_with(
            data=mock.ANY,
            collection=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_not_exists=True,
        )

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.WAITING
        )
        self.assertTrue(
            experiment.changes.filter(
                old_publish_status=NimbusExperiment.PublishStatus.APPROVED,
                new_publish_status=NimbusExperiment.PublishStatus.WAITING,
                message=NimbusChangeLog.Messages.LAUNCHING_TO_KINTO,
            ).exists()
        )
        self.assertIsNotNone(experiment.published_date)

    def test_push_experiment_to_kinto_overwrites_existing_published_date_for_draft(self):
        existing_published_date = timezone.now()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=existing_published_date,
        )

        tasks.nimbus_push_experiment_to_kinto(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
        )

        self.mock_kinto_client.create_record.assert_called_with(
            data=mock.ANY,
            collection=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_not_exists=True,
        )

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.WAITING
        )
        self.assertTrue(
            experiment.changes.filter(
                old_publish_status=NimbusExperiment.PublishStatus.APPROVED,
                new_publish_status=NimbusExperiment.PublishStatus.WAITING,
                message=NimbusChangeLog.Messages.LAUNCHING_TO_KINTO,
            ).exists()
        )
        self.assertIsNotNone(experiment.published_date)
        self.assertNotEqual(experiment.published_date, existing_published_date)

    def test_push_experiment_to_kinto_reraises_exception(self):
        experiment = NimbusExperimentFactory.create(
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
        )
        self.mock_kinto_client.create_record.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.nimbus_push_experiment_to_kinto(
                settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
            )


class TestNimbusUpdateExperimentInKinto(MockKintoClientMixin, TestCase):
    def test_updates_experiment_record_in_kinto(self):
        existing_published_date = timezone.now()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            published_date=existing_published_date,
        )

        tasks.nimbus_update_experiment_in_kinto(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
        )

        data = NimbusExperimentSerializer(experiment).data

        self.mock_kinto_client.update_record.assert_called_with(
            data=data,
            collection=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_match='"0"',
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            data={"status": KINTO_REVIEW_STATUS},
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.WAITING
        )

        self.assertTrue(
            experiment.changes.filter(
                old_publish_status=NimbusExperiment.PublishStatus.APPROVED,
                new_publish_status=NimbusExperiment.PublishStatus.WAITING,
                message=NimbusChangeLog.Messages.UPDATING_IN_KINTO,
            ).exists()
        )
        self.assertEqual(experiment.published_date, existing_published_date)

    def test_push_experiment_to_kinto_reraises_exception(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
        )
        self.mock_kinto_client.update_record.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.nimbus_update_experiment_in_kinto(
                settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
            )


class TestNimbusEndExperimentInKinto(MockKintoClientMixin, TestCase):
    def test_exception_for_failed_delete(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.mock_kinto_client.delete_record.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.nimbus_end_experiment_in_kinto(
                settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
            )

    def test_end_experiment_in_kinto_deletes_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        tasks.nimbus_end_experiment_in_kinto(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
        )

        self.mock_kinto_client.delete_record.assert_called_with(
            id=experiment.slug,
            collection=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            data={"status": KINTO_REVIEW_STATUS},
        )

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.WAITING
        )
        self.assertTrue(
            experiment.changes.filter(
                old_publish_status=NimbusExperiment.PublishStatus.APPROVED,
                new_publish_status=NimbusExperiment.PublishStatus.WAITING,
                message=NimbusChangeLog.Messages.DELETING_FROM_KINTO,
            ).exists()
        )


class TestNimbusSynchronizePreviewExperimentsInKinto(MockKintoClientMixin, TestCase):
    def test_publishes_preview_experiments_and_unpublishes_non_preview_experiments(
        self,
    ):
        should_publish_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
        )
        should_unpublish_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        self.setup_kinto_get_main_records([should_unpublish_experiment.slug])

        tasks.nimbus_synchronize_preview_experiments_in_kinto()

        data = NimbusExperimentSerializer(should_publish_experiment).data

        should_publish_experiment = NimbusExperiment.objects.get(
            id=should_publish_experiment.id
        )
        self.assertEqual(should_publish_experiment.published_dto, data)

        should_unpublish_experiment = NimbusExperiment.objects.get(
            id=should_unpublish_experiment.id
        )

        self.mock_kinto_client.create_record.assert_called_with(
            data=data,
            collection=settings.KINTO_COLLECTION_NIMBUS_PREVIEW,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_not_exists=True,
        )
        self.mock_kinto_client.delete_record.assert_called_with(
            id=should_unpublish_experiment.slug,
            collection=settings.KINTO_COLLECTION_NIMBUS_PREVIEW,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

    def test_reraises_exception(self):
        self.mock_kinto_client.create_record.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.nimbus_synchronize_preview_experiments_in_kinto()


class TestNimbusSendEmails(MockKintoClientMixin, TestCase):
    def test_enrollment_ending_email_not_sent_for_experiments_before_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            proposed_duration=20,
            with_latest_change_now=True,
        )

        tasks.nimbus_send_emails()

        self.assertEqual(experiment.emails.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_enrollment_ending_email_not_sent_for_experiments_already_sent(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=0,
            proposed_duration=20,
            with_latest_change_now=True,
        )

        NimbusEmail.objects.create(
            experiment=experiment, type=NimbusExperiment.EmailType.ENROLLMENT_END
        )

        tasks.nimbus_send_emails()

        self.assertEqual(experiment.emails.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_enrollment_ending_email_sent_for_experiments_after_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=0,
            proposed_duration=20,
            with_latest_change_now=True,
            is_rollout=False,
        )

        tasks.nimbus_send_emails()

        self.assertTrue(
            experiment.emails.filter(
                type=NimbusExperiment.EmailType.ENROLLMENT_END
            ).exists()
        )
        self.assertEqual(experiment.emails.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_enrollment_ending_email_not_sent_for_rollouts_after_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=0,
            proposed_duration=20,
            with_latest_change_now=True,
            is_rollout=True,
        )

        tasks.nimbus_send_emails()

        self.assertFalse(
            experiment.emails.filter(
                type=NimbusExperiment.EmailType.ENROLLMENT_END
            ).exists()
        )
        self.assertEqual(experiment.emails.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_experiment_ending_email_not_sent_for_experiments_before_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            proposed_duration=20,
            with_latest_change_now=True,
        )

        tasks.nimbus_send_emails()

        self.assertEqual(experiment.emails.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_experiment_ending_email_not_sent_for_experiments_already_sent(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            proposed_duration=0,
            with_latest_change_now=True,
        )

        NimbusEmail.objects.create(
            experiment=experiment, type=NimbusExperiment.EmailType.EXPERIMENT_END
        )

        tasks.nimbus_send_emails()

        self.assertEqual(experiment.emails.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_experiment_ending_email_sent_for_experiments_after_enrollment_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
            proposed_duration=0,
            with_latest_change_now=True,
        )

        tasks.nimbus_send_emails()

        self.assertTrue(
            experiment.emails.filter(
                type=NimbusExperiment.EmailType.EXPERIMENT_END
            ).exists()
        )
        self.assertEqual(experiment.emails.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
