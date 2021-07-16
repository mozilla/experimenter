import datetime

import mock
from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings

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
        for collection in NimbusExperiment.KINTO_COLLECTION_APPLICATIONS.keys():
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
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            NimbusExperimentFactory.Lifecycles.ENDING_REVIEW_REQUESTED,
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
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

    @override_settings(KINTO_REVIEW_TIMEOUT=60)
    def test_check_with_pending_review_before_timeout_aborts_early(
        self,
    ):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )

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
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

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
        pending_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

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
        pending_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

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
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

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
        rejected_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

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
        rejected_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

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

        self.assertTrue(
            rejected_experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )

    def test_check_with_approved_update_sets_experiment_to_idle_saves_published_dto(self):
        updated_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            published_dto=None,
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
            updated_experiment.published_dto, {"id": updated_experiment.slug}
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

    def test_check_with_missing_review_and_queued_launch_rolls_back_and_pushes(self):
        launching_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

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


class TestNimbusPushExperimentToKintoTask(MockKintoClientMixin, TestCase):
    def test_push_experiment_to_kinto_sends_desktop_experiment_data_and_sets_accepted(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        tasks.nimbus_push_experiment_to_kinto(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
        )

        data = NimbusExperimentSerializer(experiment).data

        self.mock_kinto_client.create_record.assert_called_with(
            data=data,
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
                message="Pushed to Kinto",
            ).exists()
        )

    def test_push_experiment_to_kinto_sends_fenix_experiment_data(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        tasks.nimbus_push_experiment_to_kinto(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
        )

        data = NimbusExperimentSerializer(experiment).data

        self.mock_kinto_client.create_record.assert_called_with(
            data=data,
            collection=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_not_exists=True,
        )

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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PAUSING_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
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
                old_publish_status=NimbusExperiment.PublishStatus.IDLE,
                new_publish_status=NimbusExperiment.PublishStatus.WAITING,
                message="Updated in Kinto",
            ).exists()
        )

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
                message=NimbusChangeLog.Messages.DELETED_FROM_KINTO,
            ).exists()
        )


class TestNimbusCheckExperimentsAreLive(MockKintoClientMixin, TestCase):
    def test_experiment_updates_when_record_is_in_main(self):
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
        )
        experiment3 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        initial_change_count = experiment3.changes.count()

        self.setup_kinto_get_main_records([experiment1.slug])
        tasks.nimbus_check_experiments_are_live()

        self.assertEqual(experiment3.changes.count(), initial_change_count)

        experiment1 = NimbusExperiment.objects.get(id=experiment1.id)
        self.assertEqual(experiment1.published_dto, {"id": experiment1.slug})

        self.assertTrue(
            experiment1.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.DRAFT,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )

        self.assertFalse(
            experiment2.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.DRAFT,
                new_status=NimbusExperiment.Status.LIVE,
            ).exists()
        )


class TestNimbusCheckExperimentsAreComplete(MockKintoClientMixin, TestCase):
    def test_experiment_updates_when_record_is_not_in_main(self):
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_WAITING,
        )
        experiment3 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        initial_change_count = experiment3.changes.count()

        self.setup_kinto_get_main_records([experiment1.slug])
        tasks.nimbus_check_experiments_are_complete()

        self.assertEqual(experiment3.changes.count(), initial_change_count)

        self.assertTrue(
            NimbusExperiment.objects.filter(
                id=experiment1.id,
                status=NimbusExperiment.Status.LIVE,
                publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )
        self.assertTrue(
            NimbusExperiment.objects.filter(
                id=experiment2.id,
                status=NimbusExperiment.Status.COMPLETE,
                publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )
        self.assertTrue(
            NimbusExperiment.objects.filter(
                id=experiment3.id,
                status=NimbusExperiment.Status.DRAFT,
                publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )

        self.assertFalse(
            experiment1.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                new_status=NimbusExperiment.Status.COMPLETE,
                message=NimbusChangeLog.Messages.COMPLETED,
            ).exists()
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

    def test_experiment_ending_email_not_sent_for_experiments_before_proposed_end_date(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_duration=10,
        )
        self.assertEqual(experiment.emails.count(), 0)
        self.setup_kinto_get_main_records([experiment.slug])
        tasks.nimbus_check_experiments_are_complete()
        self.assertEqual(experiment.emails.count(), 0)

    def test_experiment_ending_email_sent_for_experiments_past_proposed_end_date(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_duration=10,
        )
        experiment.changes.filter(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        ).update(changed_on=datetime.datetime.now() - datetime.timedelta(days=10))

        self.assertEqual(experiment.emails.count(), 0)

        self.setup_kinto_get_main_records([experiment.slug])
        tasks.nimbus_check_experiments_are_complete()

        self.assertTrue(
            experiment.emails.filter(
                type=NimbusExperiment.EmailType.EXPERIMENT_END
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_only_completes_experiments_with_matching_application_collection(self):
        desktop_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )
        fenix_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            application=NimbusExperiment.Application.FENIX,
        )

        def get_records(bucket, collection):
            if collection == settings.KINTO_COLLECTION_NIMBUS_DESKTOP:
                return [{"id": desktop_experiment.slug}]
            if collection == settings.KINTO_COLLECTION_NIMBUS_MOBILE:
                return [{"id": fenix_experiment.slug}]

        self.mock_kinto_client.get_records.side_effect = get_records
        tasks.nimbus_check_experiments_are_complete()

        self.assertTrue(
            NimbusExperiment.objects.filter(
                id=desktop_experiment.id, status=NimbusExperiment.Status.LIVE
            ).exists()
        )
        self.assertTrue(
            NimbusExperiment.objects.filter(
                id=fenix_experiment.id, status=NimbusExperiment.Status.LIVE
            ).exists()
        )


class TestNimbusSynchronizePreviewExperimentsInKinto(MockKintoClientMixin, TestCase):
    def test_publishes_preview_experiments_and_unpublishes_non_preview_experiments(self):
        should_publish_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
        )
        should_unpublish_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        self.setup_kinto_get_main_records([should_unpublish_experiment.slug])

        tasks.nimbus_synchronize_preview_experiments_in_kinto()

        data = NimbusExperimentSerializer(should_publish_experiment).data

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


class TestNimbusSendEndEnrollmentEmail(MockKintoClientMixin, TestCase):
    def test_sends_emails_for_live_experiments_past_proposed_enrollment_end_date(
        self,
    ):
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            proposed_enrollment=10,
        )
        experiment3 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
        )
        experiment3.changes.filter(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        ).update(changed_on=datetime.datetime.now() - datetime.timedelta(days=10))

        tasks.nimbus_send_end_enrollment_email()

        self.assertEqual(experiment1.emails.count(), 0)
        self.assertEqual(experiment2.emails.count(), 0)

        self.assertTrue(
            experiment3.emails.filter(
                type=NimbusExperiment.EmailType.ENROLLMENT_END
            ).exists()
        )
        self.assertEqual(experiment3.emails.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_does_not_send_email_if_already_sent(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            proposed_enrollment=10,
        )
        experiment.changes.filter(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        ).update(changed_on=datetime.datetime.now() - datetime.timedelta(days=10))
        NimbusEmail.objects.create(
            experiment=experiment, type=NimbusExperiment.EmailType.ENROLLMENT_END
        )

        tasks.nimbus_send_end_enrollment_email()

        self.assertEqual(experiment.emails.count(), 1)
        self.assertEqual(len(mail.outbox), 0)
