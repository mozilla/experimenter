import datetime

import mock
from django.conf import settings
from django.core import mail
from django.test import TestCase

from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusChangeLog, NimbusExperiment
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

        mock_end_task_patcher = mock.patch(
            "experimenter.kinto.tasks.nimbus_end_experiment_in_kinto.delay"
        )
        self.mock_end_task = mock_end_task_patcher.start()
        self.addCleanup(mock_end_task_patcher.stop)

        mock_pause_task_patcher = mock.patch(
            "experimenter.kinto.tasks.nimbus_pause_experiment_in_kinto.delay"
        )
        self.mock_pause_task = mock_pause_task_patcher.start()
        self.addCleanup(mock_pause_task_patcher.stop)

    def test_check_with_empty_queue_pushes_nothing(self):
        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )
        self.mock_kinto_client.patch_collection.assert_not_called()
        self.mock_push_task.assert_not_called()
        self.mock_pause_task.assert_not_called()
        self.mock_end_task.assert_not_called()

    def test_check_with_no_approved_publish_status_pushes_nothing(self):
        for status in [NimbusExperiment.Status.DRAFT, NimbusExperiment.Status.LIVE]:
            for publish_status in [
                NimbusExperiment.PublishStatus.IDLE,
                NimbusExperiment.PublishStatus.REVIEW,
                NimbusExperiment.PublishStatus.WAITING,
            ]:
                NimbusExperimentFactory.create_with_status(
                    status,
                    publish_status=publish_status,
                    application=NimbusExperiment.Application.DESKTOP,
                )

        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )
        self.mock_kinto_client.patch_collection.assert_not_called()
        self.mock_push_task.assert_not_called()
        self.mock_pause_task.assert_not_called()
        self.mock_end_task.assert_not_called()

    def test_check_with_approved_launch_and_no_kinto_pending_pushes_experiment(
        self,
    ):
        launching_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )
        self.mock_push_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, launching_experiment.id
        )

    def test_check_with_approved_end_and_no_kinto_pending_ends_experiment(self):
        ending_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
            application=NimbusExperiment.Application.DESKTOP,
            is_end_requested=True,
        )

        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )
        self.mock_end_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, ending_experiment.id
        )

    def test_check_with_pause_and_no_kinto_pending_pauses_experiment(self):
        pausing_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        for change in pausing_experiment.changes.all():
            change.changed_on = change.changed_on - datetime.timedelta(
                days=pausing_experiment.proposed_enrollment + 1
            )
            change.save()

        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )
        self.mock_pause_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, pausing_experiment.id
        )

    def test_check_with_timeout_launch_review_and_queued_launch_rolls_back_and_pushes(
        self,
    ):
        pending_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )
        launching_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
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

    def test_check_with_pending_pause_review_and_queued_launch_aborts_early(
        self,
    ):
        pausing_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )
        for change in pausing_experiment.changes.all():
            change.changed_on = change.changed_on - datetime.timedelta(
                days=pausing_experiment.proposed_enrollment + 1
            )
            change.save()

        NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.setup_kinto_pending_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_kinto_client.patch_collection.assert_not_called()
        self.mock_push_task.assert_not_called()
        self.mock_pause_task.assert_not_called()
        self.mock_end_task.assert_not_called()

    def test_check_with_timeout_end_review_and_queued_launch_rolls_back_and_pushes(
        self,
    ):
        pending_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            is_end_requested=True,
        )
        launching_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
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
        self.assertFalse(pending_experiment.is_end_requested)
        self.assertTrue(
            pending_experiment.changes.filter(
                old_status=NimbusExperiment.Status.LIVE,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.REVIEW,
            ).exists()
        )

    def test_check_with_rejected_launch_rolls_back_and_pushes(self):
        rejected_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )
        launching_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
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

        self.assertTrue(
            rejected_experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.DRAFT,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.DRAFT,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )

    def test_check_with_rejected_pause_rolls_back_and_pushes_same_pause(self):
        pausing_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.WAITING,
            application=NimbusExperiment.Application.DESKTOP,
        )
        for change in pausing_experiment.changes.all():
            change.changed_on = change.changed_on - datetime.timedelta(
                days=pausing_experiment.proposed_enrollment + 1
            )
            change.save()

        self.setup_kinto_rejected_review()

        tasks.nimbus_check_kinto_push_queue_by_collection(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP
        )

        self.mock_pause_task.assert_called_with(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, pausing_experiment.id
        )
        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            data={"status": KINTO_ROLLBACK_STATUS},
        )

    def test_check_with_rejected_end_rolls_back_and_pushes(self):
        rejected_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.WAITING,
            application=NimbusExperiment.Application.DESKTOP,
            is_end_requested=True,
        )
        launching_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
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
        self.assertFalse(rejected_experiment.is_end_requested)

        self.assertTrue(
            rejected_experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                old_publish_status=NimbusExperiment.PublishStatus.WAITING,
                new_status=NimbusExperiment.Status.LIVE,
                new_publish_status=NimbusExperiment.PublishStatus.IDLE,
            ).exists()
        )

    def test_check_with_missing_review_and_queued_launch_rolls_back_and_pushes(self):
        launching_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
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
        launching_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
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
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
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
        experiment = NimbusExperimentFactory.create(
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
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


class TestNimbusPauseExperimentInKinto(MockKintoClientMixin, TestCase):
    def test_updates_experiment_record_isEnrollmentPaused_true_in_kinto(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            proposed_enrollment=10,
            application=NimbusExperiment.Application.DESKTOP,
        )
        launch_change = experiment.changes.get(
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.LIVE,
        )
        launch_change.changed_on = datetime.datetime.now() - datetime.timedelta(days=11)
        launch_change.save()

        self.mock_kinto_client.get_records.return_value = [
            {"id": experiment.slug, "isEnrollmentPaused": False}
        ]

        tasks.nimbus_pause_experiment_in_kinto(
            settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
        )

        data = NimbusExperimentSerializer(experiment).data
        data["isEnrollmentPaused"] = True

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

    def test_push_experiment_to_kinto_reraises_exception(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
        )
        self.mock_kinto_client.get_records.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.nimbus_pause_experiment_in_kinto(
                settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
            )


class TestNimbusEndExperimentInKinto(MockKintoClientMixin, TestCase):
    def test_exception_for_failed_delete(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.mock_kinto_client.delete_record.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.nimbus_end_experiment_in_kinto(
                settings.KINTO_COLLECTION_NIMBUS_DESKTOP, experiment.id
            )

    def test_end_experiment_in_kinto_deletes_experiment(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
            is_end_requested=True,
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
        experiment1 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.WAITING,
        )

        experiment2 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.WAITING,
        )

        experiment3 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
        )

        self.assertEqual(experiment1.changes.count(), 1)
        self.assertEqual(experiment2.changes.count(), 1)
        self.assertEqual(experiment3.changes.count(), 1)

        self.setup_kinto_get_main_records([experiment1.slug])
        tasks.nimbus_check_experiments_are_live()

        self.assertEqual(experiment3.changes.count(), 1)

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


class TestNimbusCheckExperimentsArePaused(MockKintoClientMixin, TestCase):
    def test_ignores_unpaused_experiment_with_isEnrollmentPaused_false(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.DESKTOP,
            is_paused=False,
        )
        changes_count = experiment.changes.count()

        self.mock_kinto_client.get_records.return_value = [
            {"id": experiment.slug, "isEnrollmentPaused": False}
        ]

        tasks.nimbus_check_experiments_are_paused()

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertFalse(experiment.is_paused)
        self.assertEqual(experiment.changes.count(), changes_count)

    def test_updates_unpaused_experiment_with_isEnrollmentPaused_true(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.DESKTOP,
            is_paused=False,
        )
        changes_count = experiment.changes.count()

        self.mock_kinto_client.get_records.return_value = [
            {"id": experiment.slug, "isEnrollmentPaused": True}
        ]

        tasks.nimbus_check_experiments_are_paused()

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertTrue(experiment.is_paused)
        self.assertEqual(experiment.changes.count(), changes_count + 1)
        self.assertTrue(
            experiment.changes.filter(message=NimbusChangeLog.Messages.PAUSED).exists()
        )

    def test_ignores_paused_experiment_with_isEnrollmentPaused_true(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.DESKTOP,
            is_paused=True,
        )
        changes_count = experiment.changes.count()

        self.mock_kinto_client.get_records.return_value = [
            {"id": experiment.slug, "isEnrollmentPaused": True}
        ]

        tasks.nimbus_check_experiments_are_paused()

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertTrue(experiment.is_paused)
        self.assertEqual(experiment.changes.count(), changes_count)


class TestNimbusCheckExperimentsAreComplete(MockKintoClientMixin, TestCase):
    def test_experiment_updates_when_record_is_not_in_main(self):
        experiment1 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

        experiment2 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.WAITING,
        )

        experiment3 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

        self.assertEqual(experiment1.changes.count(), 2)
        self.assertEqual(experiment2.changes.count(), 2)
        self.assertEqual(experiment3.changes.count(), 1)

        self.setup_kinto_get_main_records([experiment1.slug])
        tasks.nimbus_check_experiments_are_complete()

        self.assertEqual(experiment3.changes.count(), 1)

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
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            proposed_duration=10,
        )
        self.assertEqual(experiment.emails.count(), 0)
        self.setup_kinto_get_main_records([experiment.slug])
        tasks.nimbus_check_experiments_are_complete()
        self.assertEqual(experiment.emails.count(), 0)

    def test_experiment_ending_email_sent_for_experiments_past_proposed_end_date(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
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
        desktop_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.DESKTOP,
        )
        fenix_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
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
        should_publish_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.PREVIEW
        )
        should_unpublish_experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT
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
