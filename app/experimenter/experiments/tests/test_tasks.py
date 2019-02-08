from smtplib import SMTPException

from django.conf import settings
from django.test import TestCase
from requests.exceptions import RequestException

from experimenter.experiments import bugzilla
from experimenter.experiments.models import Experiment
from experimenter.experiments import tasks
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.tests.mixins import (
    MockBugzillaMixin,
    MockMailMixin,
    MockRequestMixin,
)
from experimenter.notifications.models import Notification


class TestSendReviewEmailTask(MockRequestMixin, MockMailMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )

    def test_successful_email_creates_notification(self):
        self.assertEqual(Notification.objects.count(), 0)

        tasks.send_review_email_task(
            self.user.id,
            self.experiment.name,
            self.experiment.experiment_url,
            False,
        )

        self.mock_send_mail.assert_called()

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

        self.mock_send_mail.side_effect = SMTPException()

        with self.assertRaises(SMTPException):
            tasks.send_review_email_task(
                self.user.id,
                self.experiment.name,
                self.experiment.experiment_url,
                False,
            )

        self.mock_send_mail.assert_called()

        self.assertEqual(Notification.objects.count(), 0)


class TestCreateBugTask(MockRequestMixin, MockBugzillaMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )

    def test_experiment_bug_successfully_created(self):
        self.assertEqual(Notification.objects.count(), 0)

        tasks.create_experiment_bug_task(self.user.id, self.experiment.id)

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
            tasks.create_experiment_bug_task(self.user.id, self.experiment.id)

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

        tasks.add_experiment_comment_task(self.user.id, self.experiment.id)

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
            tasks.add_experiment_comment_task(self.user.id, self.experiment.id)

        self.mock_bugzilla_requests_post.assert_called()
        self.assertEqual(Notification.objects.count(), 0)
