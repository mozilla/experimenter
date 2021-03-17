import datetime

import mock
from django.conf import settings
from django.core import mail
from django.test import TestCase

from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.kinto import tasks
from experimenter.kinto.client import (
    KINTO_REJECTED_STATUS,
    KINTO_REVIEW_STATUS,
    KINTO_ROLLBACK_STATUS,
)
from experimenter.kinto.tests.mixins import MockKintoClientMixin


class TestPushExperimentToKintoTask(MockKintoClientMixin, TestCase):
    def test_push_experiment_to_kinto_sends_desktop_experiment_data_and_sets_accepted(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.REVIEW,
            application=NimbusExperiment.Application.DESKTOP,
        )

        tasks.nimbus_push_experiment_to_kinto(experiment.id)

        data = NimbusExperimentSerializer(experiment).data

        self.mock_kinto_client.create_record.assert_called_with(
            data=data,
            collection=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_not_exists=True,
        )

        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.status, NimbusExperiment.Status.ACCEPTED)
        self.assertTrue(
            experiment.changes.filter(
                old_status=NimbusExperiment.Status.REVIEW,
                new_status=NimbusExperiment.Status.ACCEPTED,
            ).exists()
        )

    def test_push_experiment_to_kinto_sends_fenix_experiment_data(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.REVIEW,
            application=NimbusExperiment.Application.FENIX,
        )

        tasks.nimbus_push_experiment_to_kinto(experiment.id)

        data = NimbusExperimentSerializer(experiment).data

        self.mock_kinto_client.create_record.assert_called_with(
            data=data,
            collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_not_exists=True,
        )

    def test_push_experiment_to_kinto_reraises_exception(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.REVIEW,
        )
        self.mock_kinto_client.create_record.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.nimbus_push_experiment_to_kinto(experiment.id)


class TestCheckKintoPushQueue(MockKintoClientMixin, TestCase):
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
        tasks.nimbus_check_kinto_push_queue()
        self.mock_push_task.assert_not_called()
        self.mock_end_task.assert_not_called()

    def test_check_experiment_with_no_review_status_pushes_nothing(self):
        for status in [
            NimbusExperiment.Status.DRAFT,
            NimbusExperiment.Status.ACCEPTED,
            NimbusExperiment.Status.LIVE,
            NimbusExperiment.Status.COMPLETE,
        ]:
            NimbusExperimentFactory.create(status=status)

        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue()
        self.mock_push_task.assert_not_called()
        self.mock_end_task.assert_not_called()

    def test_check_experiment_with_review_and_kinto_pending_pushes_nothing(self):
        NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.REVIEW,
        )
        self.setup_kinto_pending_review()
        tasks.nimbus_check_kinto_push_queue()
        self.mock_push_task.assert_not_called()
        self.mock_end_task.assert_not_called()

    def test_checkexperiment_with_review_and_no_kinto_pending_pushes_experiment(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.REVIEW
        )
        self.assertEqual(experiment.changes.count(), 2)

        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue()
        self.mock_push_task.assert_called_with(experiment.id)

    def test_check_with_reject_review(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.mock_kinto_client.get_collection.side_effect = [
            # Desktop responses
            {
                "data": {
                    "status": KINTO_REJECTED_STATUS,
                    "last_reviewer_comment": "it's no good",
                }
            },
            {"data": {"status": "anything"}},
            # Fenix responses
            {"data": {"status": "anything"}},
            {"data": {"status": "anything"}},
        ]
        self.mock_kinto_client.get_records.side_effect = [
            # Desktop responses
            [{"id": "another-experiment"}],
            [
                {"id": "another-experiment"},
                {"id": experiment.slug},
            ],
            # Fenix responses
            [],
            [],
        ]
        tasks.nimbus_check_kinto_push_queue()

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            data={"status": KINTO_ROLLBACK_STATUS},
        )

        self.assertTrue(
            experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.ACCEPTED,
                new_status=NimbusExperiment.Status.DRAFT,
            ).exists()
        )

    def test_check_with_reject_review_doesnt_draft_non_accepted(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            is_end_requested=False,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.mock_kinto_client.get_collection.side_effect = [
            # Desktop responses
            {
                "data": {
                    "status": KINTO_REJECTED_STATUS,
                    "last_reviewer_comment": "it's no good",
                }
            },
            {"data": {"status": "anything"}},
            # Fenix responses
            {"data": {"status": "anything"}},
            {"data": {"status": "anything"}},
        ]
        self.mock_kinto_client.get_records.side_effect = [
            # Desktop responses
            [{"id": "another-experiment"}],
            [
                {"id": "another-experiment"},
                {"id": experiment.slug},
            ],
            # Fenix responses
            [],
            [],
        ]
        tasks.nimbus_check_kinto_push_queue()

        # It still rolls back
        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            data={"status": KINTO_ROLLBACK_STATUS},
        )

        # But it does not revert to draft
        self.assertFalse(
            experiment.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                new_status=NimbusExperiment.Status.DRAFT,
            ).exists()
        )

    def test_check_live_end_requested_with_reject_review(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            is_end_requested=True,
            application=NimbusExperiment.Application.DESKTOP,
        )

        rejection_message = "can't end this yet"
        self.mock_kinto_client.get_collection.side_effect = [
            # Desktop responses
            {
                "data": {
                    "status": KINTO_REJECTED_STATUS,
                    "last_reviewer_comment": rejection_message,
                }
            },
            {"data": {"status": "anything"}},
            # Fenix responses
            {"data": {"status": "anything"}},
            {"data": {"status": "anything"}},
        ]
        self.mock_kinto_client.get_records.side_effect = [
            # Desktop responses
            [{"id": "another-experiment"}],
            [
                {"id": "another-experiment"},
                {"id": experiment.slug},
            ],
            # Fenix responses
            [],
            [],
        ]
        tasks.nimbus_check_kinto_push_queue()

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            data={"status": KINTO_ROLLBACK_STATUS},
        )

        self.assertTrue(
            NimbusExperiment.objects.filter(
                id=experiment.id,
                status=NimbusExperiment.Status.LIVE,
                is_end_requested=False,
            ).exists()
        )

        latest_change = experiment.changes.order_by("-changed_on").first()
        self.assertFalse(latest_change.experiment_data["is_end_requested"])
        self.assertEqual(latest_change.message, f"Rejected: {rejection_message}")

    def test_check_can_rejection_and_still_push_changes(self):
        experiment1 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            is_end_requested=True,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment2 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.REVIEW,
            application=NimbusExperiment.Application.DESKTOP,
        )

        self.mock_kinto_client.get_collection.side_effect = [
            # Desktop responses
            {
                "data": {
                    "status": KINTO_REJECTED_STATUS,
                    "last_reviewer_comment": "can't end this yet",
                }
            },
            {"data": {"status": "anything"}},
            # Fenix responses
            {"data": {"status": "anything"}},
            {"data": {"status": "anything"}},
        ]
        self.mock_kinto_client.get_records.side_effect = [
            # Desktop responses
            [{"id": "another-experiment"}],
            [
                {"id": "another-experiment"},
                {"id": experiment1.slug},
            ],
            # Fenix responses
            [],
            [],
        ]
        tasks.nimbus_check_kinto_push_queue()

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            data={"status": KINTO_ROLLBACK_STATUS},
        )

        self.assertTrue(
            NimbusExperiment.objects.filter(
                id=experiment1.id,
                status=NimbusExperiment.Status.LIVE,
                is_end_requested=False,
            ).exists()
        )

        self.mock_push_task.assert_called_with(experiment2.id)

    def test_check_experiment_with_end_requested_and_no_kinto_pending_ends_experiment(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.DESKTOP,
            is_end_requested=True,
        )
        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue()
        self.mock_end_task.assert_called_with(experiment.id)

    def test_check_experiment_pushes_experiment_before_ending_experiment(
        self,
    ):
        experiment_1 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.REVIEW,
            name="First experiment",
            slug="first-experiment",
            application=NimbusExperiment.Application.FENIX,
        )
        experiment_2 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            name="Second experiment",
            slug="second-experiment",
            application=NimbusExperiment.Application.FENIX,
            is_end_requested=True,
        )

        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue()
        self.mock_push_task.assert_called_with(experiment_1.id)
        self.mock_end_task.assert_not_called()

        experiment_1.status = NimbusExperiment.Status.LIVE
        experiment_1.save()

        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue()
        self.mock_end_task.assert_called_with(experiment_2.id)

    def test_check_experiment_that_should_pause_does_pause(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            proposed_enrollment=10,
            is_paused=False,
            application=NimbusExperiment.Application.DESKTOP,
        )
        launch_change = experiment.changes.get(
            old_status=NimbusExperiment.Status.ACCEPTED,
            new_status=NimbusExperiment.Status.LIVE,
        )
        launch_change.changed_on = datetime.datetime.now() - datetime.timedelta(days=11)
        launch_change.save()

        self.setup_kinto_no_pending_review()
        tasks.nimbus_check_kinto_push_queue()

        self.mock_pause_task.assert_called_with(experiment.id)


class TestCheckExperimentIsLive(MockKintoClientMixin, TestCase):
    def test_experiment_updates_when_record_is_in_main(self):
        experiment1 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
        )

        experiment2 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
        )

        experiment3 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
        )

        self.assertEqual(experiment1.changes.count(), 3)
        self.assertEqual(experiment2.changes.count(), 3)
        self.assertEqual(experiment3.changes.count(), 1)

        self.setup_kinto_get_main_records([experiment1.slug])
        tasks.nimbus_check_experiments_are_live()

        self.assertEqual(experiment3.changes.count(), 1)

        self.assertTrue(
            experiment1.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.ACCEPTED,
                new_status=NimbusExperiment.Status.LIVE,
            ).exists()
        )

        self.assertFalse(
            experiment2.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.ACCEPTED,
                new_status=NimbusExperiment.Status.LIVE,
            ).exists()
        )


class TestCheckExperimentIsComplete(MockKintoClientMixin, TestCase):
    def test_experiment_updates_when_record_is_not_in_main(self):
        experiment1 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
        )

        experiment2 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
        )

        experiment3 = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
        )

        self.assertEqual(experiment1.changes.count(), 4)
        self.assertEqual(experiment2.changes.count(), 4)
        self.assertEqual(experiment3.changes.count(), 1)

        self.setup_kinto_get_main_records([experiment1.slug])
        tasks.nimbus_check_experiments_are_complete()

        self.assertEqual(experiment3.changes.count(), 1)

        self.assertTrue(
            NimbusExperiment.objects.filter(
                id=experiment1.id, status=NimbusExperiment.Status.LIVE
            ).exists()
        )
        self.assertTrue(
            NimbusExperiment.objects.filter(
                id=experiment2.id, status=NimbusExperiment.Status.COMPLETE
            ).exists()
        )
        self.assertTrue(
            NimbusExperiment.objects.filter(
                id=experiment3.id, status=NimbusExperiment.Status.DRAFT
            ).exists()
        )

        self.assertFalse(
            experiment1.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                new_status=NimbusExperiment.Status.COMPLETE,
            ).exists()
        )

        self.assertTrue(
            experiment2.changes.filter(
                changed_by__email=settings.KINTO_DEFAULT_CHANGELOG_USER,
                old_status=NimbusExperiment.Status.LIVE,
                new_status=NimbusExperiment.Status.COMPLETE,
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
            old_status=NimbusExperiment.Status.ACCEPTED,
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


class TestEndExperimentInKinto(MockKintoClientMixin, TestCase):
    def test_exception_for_failed_delete(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
        )
        self.mock_kinto_client.delete_record.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.nimbus_end_experiment_in_kinto(experiment.id)

    def test_end_experiment_in_kinto_deletes_experiment(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        tasks.nimbus_end_experiment_in_kinto(experiment.id)

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


class TestNimbusPauseExperimentInKinto(MockKintoClientMixin, TestCase):
    def test_updates_experiment_record_isEnrollmentPaused_true_in_kinto(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
            proposed_enrollment=10,
            application=NimbusExperiment.Application.DESKTOP,
        )
        launch_change = experiment.changes.get(
            old_status=NimbusExperiment.Status.ACCEPTED,
            new_status=NimbusExperiment.Status.LIVE,
        )
        launch_change.changed_on = datetime.datetime.now() - datetime.timedelta(days=11)
        launch_change.save()

        self.mock_kinto_client.get_records.return_value = [{"id": experiment.slug}]
        tasks.nimbus_pause_experiment_in_kinto(experiment.id)

        self.mock_kinto_client.update_record.assert_called_with(
            data={"id": experiment.slug, "isEnrollmentPaused": True},
            collection=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_match='"0"',
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
            data={"status": KINTO_REVIEW_STATUS},
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

    def test_push_experiment_to_kinto_reraises_exception(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.LIVE,
        )
        self.mock_kinto_client.get_records.side_effect = Exception
        with self.assertRaises(Exception):
            tasks.nimbus_pause_experiment_in_kinto(experiment.id)


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
