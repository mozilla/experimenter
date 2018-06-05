import mock
from django.test import TestCase
from django.conf import settings

from experimenter.experiments.email import send_review_email
from experimenter.experiments.tests.factories import ExperimentFactory


class TestSendReviewEmail(TestCase):

    def setUp(self):
        super().setUp()
        mock_send_mail_patcher = mock.patch(
            "experimenter.experiments.email.send_mail"
        )
        self.mock_send_mail = mock_send_mail_patcher.start()
        self.addCleanup(mock_send_mail_patcher.stop)

    def test_send_review_email_without_needs_attention(self):
        experiment = ExperimentFactory.create(
            name="Experiment", slug="experiment"
        )
        send_review_email(experiment, False)
        self.mock_send_mail.assert_called_with(
            "Experimenter Review Request: Experiment",
            (
                "Please add the following experiment to the Shield review "
                "queue:\n\nhttps://localhost/experiments/experiment/\n\n"
            ),
            settings.EMAIL_SENDER,
            [settings.EMAIL_REVIEW],
            fail_silently=False,
        )

    def test_send_review_email_with_needs_attention(self):
        experiment = ExperimentFactory.create(
            name="Experiment", slug="experiment"
        )
        send_review_email(experiment, True)
        self.mock_send_mail.assert_called_with(
            "Experimenter Review Request: Experiment",
            (
                "Please add the following experiment to the Shield review "
                "queue:\n\nhttps://localhost/experiments/experiment/\n\n"
                "This experiment requires special attention and "
                "should be reviewed ASAP"
            ),
            settings.EMAIL_SENDER,
            [settings.EMAIL_REVIEW],
            fail_silently=False,
        )
