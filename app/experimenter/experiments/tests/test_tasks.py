from smtplib import SMTPException

import markus
import mock
from django.conf import settings
from django.core import mail
from django.test import TestCase
from markus.testing import MetricsMock
from requests.exceptions import RequestException

from experimenter.experiments import bugzilla, tasks
from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.tests.mixins import (
    MockBugzillaMixin,
    MockRequestMixin,
)
from experimenter.notifications.models import Notification


class TestSendReviewEmailTask(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )

    def test_successful_email_creates_notification(self):
        self.assertEqual(Notification.objects.count(), 0)

        with MetricsMock() as mm:
            tasks.send_review_email_task(
                self.user.id,
                self.experiment.name,
                self.experiment.experiment_url,
                False,
            )

            # We should get 3 stats calls firing in order of completion.
            self.assertEqual(len(mm.get_records()), 3)
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.send_review_email.started",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.send_review_email.completed",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING, "experiments.tasks.send_review_email.timing"
                )
            )
            # Failed metric should not be sent.
            self.assertFalse(
                mm.has_record(
                    markus.INCR, "experiments.tasks.send_review_email.failed"
                )
            )

        self.assertEqual(len(mail.outbox), 1)

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message,
            tasks.NOTIFICATION_MESSAGE_REVIEW_EMAIL.format(
                email=settings.EMAIL_REVIEW, name=self.experiment.name
            ),
        )

    def test_failed_email_doesnt_create_notification(self):
        self.assertEqual(Notification.objects.count(), 0)

        with mock.patch(
            "experimenter.experiments.tasks.send_review_email_task"
        ) as mocked:
            mocked.side_effect = SMTPException
            with self.assertRaises(SMTPException):
                with MetricsMock() as mm:
                    tasks.send_review_email_task(
                        self.user.id,
                        self.experiment.name,
                        self.experiment.experiment_url,
                        False,
                    )

                    self.assertTrue(
                        mm.has_record(
                            markus.INCR,
                            "experiments.tasks.send_review_email.started",
                            value=1,
                        )
                    )
                    self.assertTrue(
                        mm.has_record(
                            markus.INCR,
                            "experiments.tasks.send_review_email.failed",
                            value=1,
                        )
                    )
                    # Failures should abort timing metrics.
                    self.assertFalse(
                        mm.has_record(
                            markus.TIMING,
                            "experiments.tasks.send_review_email.timing",
                        )
                    )
                    # Completed should not be sent.
                    self.assertFalse(
                        mm.has_record(
                            markus.INCR,
                            "experiments.tasks.send_review_email.completed",
                        )
                    )

        self.assertEqual(Notification.objects.count(), 0)


class TestCreateBugTask(MockRequestMixin, MockBugzillaMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
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
                    markus.TIMING,
                    "experiments.tasks.create_experiment_bug.timing",
                )
            )
            # Failed metric should not be sent.
            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.create_experiment_bug.failed",
                )
            )

        self.mock_bugzilla_requests_post.assert_called()

        experiment = Experiment.objects.get(id=self.experiment.id)
        self.assertEqual(experiment.bugzilla_id, self.bugzilla_id)

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message,
            tasks.NOTIFICATION_MESSAGE_CREATE_BUG.format(
                bug_url=experiment.bugzilla_url
            ),
        )

    def test_bugzilla_error_creates_error_notification(self):
        self.assertEqual(Notification.objects.count(), 0)

        self.mock_bugzilla_requests_post.side_effect = RequestException()

        with self.assertRaises(bugzilla.BugzillaError):
            with MetricsMock() as mm:
                tasks.create_experiment_bug_task(
                    self.user.id, self.experiment.id
                )

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
                        markus.TIMING,
                        "experiments.tasks.create_experiment_bug.timing",
                    )
                )
                # Completed metric should not be sent.
                self.assertFalse(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.create_experiment_bug.completed",
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


class TestAddCommentTask(MockRequestMixin, MockBugzillaMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        self.experiment.bugzilla_id = self.bugzilla_id
        self.experiment.save()

    def test_experiment_bug_successfully_created(self):
        self.assertEqual(Notification.objects.count(), 0)

        with MetricsMock() as mm:
            tasks.add_experiment_comment_task(self.user.id, self.experiment.id)

            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.add_experiment_comment.started",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.add_experiment_comment.completed",
                    value=1,
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING,
                    "experiments.tasks.add_experiment_comment.timing",
                )
            )
            # Failed metric should not be sent.
            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.add_experiment_comment.failed",
                )
            )

        self.mock_bugzilla_requests_post.assert_called()

        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.message,
            tasks.NOTIFICATION_MESSAGE_ADD_COMMENT.format(
                bug_url=self.experiment.bugzilla_url
            ),
        )

    def test_bugzilla_error_doesnt_create_notification(self):
        self.assertEqual(Notification.objects.count(), 0)

        self.mock_bugzilla_requests_post.side_effect = RequestException()

        with self.assertRaises(bugzilla.BugzillaError):
            with MetricsMock() as mm:
                tasks.add_experiment_comment_task(
                    self.user.id, self.experiment.id
                )

                self.assertTrue(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.add_experiment_comment.started",
                        value=1,
                    )
                )
                self.assertTrue(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.add_experiment_comment.failed",
                        value=1,
                    )
                )
                # Failures should abort timing metrics.
                self.assertFalse(
                    mm.has_record(
                        markus.TIMING,
                        "experiments.tasks.add_experiment_comment.timing",
                    )
                )
                # Completed metric should not be sent.
                self.assertFalse(
                    mm.has_record(
                        markus.INCR,
                        "experiments.tasks.add_experiment_comment.completed",
                    )
                )

        self.mock_bugzilla_requests_post.assert_called()
        self.assertEqual(Notification.objects.count(), 0)

    def test_internal_only_does_not_add_comment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, risk_internal_only=True
        )

        with MetricsMock() as mm:
            tasks.add_experiment_comment_task(self.user.id, experiment.id)

            self.assertTrue(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.add_experiment_comment.started",
                    value=1,
                )
            )
            # Comment is aborted when internal only, so completed not sent.
            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.add_experiment_comment.completed",
                )
            )
            self.assertTrue(
                mm.has_record(
                    markus.TIMING,
                    "experiments.tasks.add_experiment_comment.timing",
                )
            )
            # Failed metric should not be sent.
            self.assertFalse(
                mm.has_record(
                    markus.INCR,
                    "experiments.tasks.add_experiment_comment.failed",
                )
            )

        self.mock_bugzilla_requests_post.assert_not_called()

        self.assertEqual(Notification.objects.count(), 0)
