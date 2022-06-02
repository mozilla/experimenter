import markus
from django.conf import settings
from django.test import TestCase
from markus.testing import MetricsMock
from requests import RequestException

from experimenter.base.tests.mixins import MockRequestMixin
from experimenter.bugzilla import client as bugzilla
from experimenter.bugzilla import tasks
from experimenter.bugzilla.tests.mixins import MockBugzillaMixin
from experimenter.legacy.legacy_experiments.models import Experiment
from experimenter.legacy.legacy_experiments.tests.factories import ExperimentFactory
from experimenter.legacy.normandy.tests.mixins import MockNormandyMixin
from experimenter.notifications.models import Notification


class TestCreateBugTask(MockRequestMixin, MockBugzillaMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, bugzilla_id=None
        )

    def test_experiment_bug_successfully_created(self):
        self.assertEqual(Notification.objects.count(), 0)

        with MetricsMock() as mm:
            tasks.create_experiment_bug_task(self.user.id, self.experiment.id)

            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.create_experiment_bug.started",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.create_experiment_bug.completed",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING, "experiments.tasks.create_experiment_bug.timing"
                )
            )
            # Failed metric should not be sent.
            self.assertFalse(
                mm.has_record(
                    markus.INCR, "experiments.tasks.create_experiment_bug.failed"
                )
            )

        self.mock_bugzilla_requests_post.assert_called()

        experiment = Experiment.objects.get(id=self.experiment.id)
        self.assertEqual(experiment.bugzilla_id, self.bugzilla_id)

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message,
            tasks.NOTIFICATION_MESSAGE_CREATE_BUG.format(bug_url=experiment.bugzilla_url),
        )

    def test_bugzilla_error_creates_error_notification(self):
        self.assertEqual(Notification.objects.count(), 0)

        self.mock_bugzilla_requests_post.side_effect = RequestException()

        with self.assertRaises(bugzilla.BugzillaError):
            with MetricsMock() as mm:
                tasks.create_experiment_bug_task(self.user.id, self.experiment.id)

                self.assertTrue(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.create_experiment_bug.started",
                        value=1,
                    )
                )
                self.assertTrue(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.create_experiment_bug.failed",
                        value=1,
                    )
                )
                # Failures should abort timing metrics.
                self.assertFalse(
                    mm.has_record(
                        markus.TIMING, "experiments.tasks.create_experiment_bug.timing"
                    )
                )
                # Completed metric should not be sent.
                self.assertFalse(
                    mm.has_record(
                        markus.INCR, "experiments.tasks.create_experiment_bug.completed"
                    )
                )

        self.mock_bugzilla_requests_post.assert_called()
        self.assertEqual(Notification.objects.count(), 1)

        experiment = Experiment.objects.get(id=self.experiment.id)
        self.assertEqual(experiment.bugzilla_id, None)

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message, tasks.NOTIFICATION_MESSAGE_CREATE_BUG_FAILED
        )


class TestUpdateResolutionTask(MockRequestMixin, MockBugzillaMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        self.experiment.bugzilla_id = self.bugzilla_id
        self.experiment.save()

    def test_experiment_bug_resolution_successfully_updated(self):
        self.assertEqual(Notification.objects.count(), 0)

        tasks.update_bug_resolution_task(self.user.id, self.experiment.id)

        self.mock_bugzilla_requests_put.assert_called()

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message,
            tasks.NOTIFICATION_MESSAGE_ARCHIVE_COMMENT.format(
                bug_url=self.experiment.bugzilla_url
            ),
        )

    def test_no_request_call_when_no_bug_id(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, risk_confidential=True
        )
        experiment.bugzilla_id = None
        experiment.save()

        tasks.update_bug_resolution_task(self.user.id, experiment.id)

        self.mock_bugzilla_requests_put.assert_not_called()

        self.assertEqual(Notification.objects.count(), 0)

    def test_bugzilla_error_create_notifications(self):
        self.assertEqual(Notification.objects.count(), 0)

        self.mock_bugzilla_requests_put.side_effect = RequestException()

        with self.assertRaises(bugzilla.BugzillaError):

            tasks.update_bug_resolution_task(self.user.id, self.experiment.id)

            self.mock_bugzilla_requests_put.side_effect = RequestException()
            self.mock_bugzilla_requests_put.assert_called()
            self.assertEqual(Notification.objects.count(), 1)
            message = tasks.NOTIFICATION_MESSAGE_ARCHIVE_ERROR_MESSAGE.format(
                bug_url=self.experiment.bugzilla_url
            )
            self.assertEqual(Notification.objects.filters(message=message).exists())


class TestUpdateTask(MockRequestMixin, MockBugzillaMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        self.experiment.bugzilla_id = self.bugzilla_id
        self.experiment.save()

    def test_experiment_bug_successfully_updated(self):
        self.assertEqual(Notification.objects.count(), 0)

        with MetricsMock() as mm:
            tasks.update_experiment_bug_task(self.user.id, self.experiment.id)

            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_bug.started",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_bug.completed",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING, "experiments.tasks.update_experiment_bug.timing"
                )
            )
            # Failed metric should not be sent.
            self.assertFalse(
                mm.has_record(
                    markus.INCR, "experiments.tasks.update_experiment_bug.failed"
                )
            )

        self.mock_bugzilla_requests_put.assert_called()

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message,
            tasks.NOTIFICATION_MESSAGE_UPDATE_BUG.format(
                bug_url=self.experiment.bugzilla_url
            ),
        )

    def test_bugzilla_error_creates_notifications(self):
        self.assertEqual(Notification.objects.count(), 0)

        self.mock_bugzilla_requests_put.side_effect = RequestException()

        with self.assertRaises(bugzilla.BugzillaError):
            with MetricsMock() as mm:
                tasks.update_experiment_bug_task(self.user.id, self.experiment.id)

                self.assertTrue(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.update_experiment_bug.started",
                        value=1,
                    )
                )
                # Failures should abort timing metrics.
                self.assertFalse(
                    mm.has_record(
                        markus.INCR, "experiments.tasks.update_experiment_bug.timing"
                    )
                )
                # Completed metric should not be sent.
                self.assertFalse(
                    mm.has_record(
                        markus.INCR, "experiments.tasks.update_experiment_bug.completed"
                    )
                )

        self.mock_bugzilla_requests_put.assert_called()
        self.assertEqual(Notification.objects.count(), 1)

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message, tasks.NOTIFICATION_MESSAGE_UPDATE_BUG_FAILED
        )

    def test_confidential_only_does_not_update_bugzilla(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, risk_confidential=True
        )

        with MetricsMock() as mm:
            tasks.update_experiment_bug_task(self.user.id, experiment.id)

            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.update_experiment_bug.started",
                    value=1,
                )
            )
            self.assertFalse(
                mm.has_record(
                    markus.INCR, "experiements.tasks.update_experiment_bug.completed"
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING, "experiments.tasks.update_experiment_bug.timing"
                )
            )

            self.assertFalse(
                mm.has_record(
                    markus.INCR, "experiments.tasks.update_experiement_bug.failed"
                )
            )

        self.mock_bugzilla_requests_put.assert_not_called()

        self.assertEqual(Notification.objects.count(), 0)


class TestUpdateExperimentSubTask(MockNormandyMixin, MockBugzillaMixin, TestCase):
    def test_add_start_date_comment_task(self):
        experiment = ExperimentFactory.create(normandy_id=12345)
        comment = "Start Date: {} End Date: {}".format(
            experiment.start_date, experiment.end_date
        )
        expected_call_data = {"comment": comment}

        tasks.add_start_date_comment_task(experiment.id)

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_COMMENT_URL.format(id=12345), expected_call_data
        )

    def test_add_start_date_comment_task_failure(self):
        experiment = ExperimentFactory.create(normandy_id=12345)

        self.mock_bugzilla_requests_post.side_effect = RequestException
        with self.assertRaises(bugzilla.BugzillaError):
            tasks.add_start_date_comment_task(experiment.id)

    def test_comp_experiment_update_res_task(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_COMPLETE, normandy_id=12345
        )

        expected_call_data = {"status": "RESOLVED", "resolution": "FIXED"}

        tasks.comp_experiment_update_res_task(experiment.id)

        self.mock_bugzilla_requests_put.assert_called_with(
            settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
            expected_call_data,
        )

    def test_comp_experiment_update_res_task_with_bug_error(self):
        self.mock_bugzilla_requests_put.side_effect = RequestException()
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_COMPLETE, normandy_id=12345
        )

        with self.assertRaises(bugzilla.BugzillaError):
            tasks.comp_experiment_update_res_task(experiment.id)
