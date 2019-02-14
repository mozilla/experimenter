from django.test import TestCase
from django.conf import settings
from django.core import mail

from experimenter.experiments.email import send_review_email
from experimenter.experiments.tests.factories import ExperimentFactory


class TestSendReviewEmail(TestCase):

    def test_send_review_email_without_needs_attention(self):
        experiment = ExperimentFactory.create(
            name="Experiment", slug="experiment"
        )
        send_review_email(experiment.name, experiment.experiment_url, False)

        sent_email = mail.outbox[-1]
        self.assertEqual(
            sent_email.subject, "Experimenter Review Request: Experiment"
        )
        self.assertEqual(
            sent_email.body,
            "Please add the following experiment to the Shield review "
            f"queue:\n\nhttps://{settings.HOSTNAME}"
            "/experiments/experiment/\n\n",
        )
        self.assertEqual(sent_email.from_email, settings.EMAIL_SENDER)
        self.assertEqual(sent_email.recipients(), [settings.EMAIL_REVIEW])

    def test_send_review_email_with_needs_attention(self):
        experiment = ExperimentFactory.create(
            name="Experiment", slug="experiment"
        )
        send_review_email(experiment.name, experiment.experiment_url, True)

        sent_email = mail.outbox[-1]
        self.assertEqual(
            sent_email.subject, "Experimenter Review Request: Experiment"
        )

        self.assertEqual(
            sent_email.body,
            "Please add the following experiment to the Shield review "
            f"queue:\n\nhttps://{settings.HOSTNAME}"
            "/experiments/experiment/\n\n"
            "This experiment requires special attention and "
            "should be reviewed ASAP",
        )
        self.assertEqual(sent_email.from_email, settings.EMAIL_SENDER)
        self.assertEqual(sent_email.recipients(), [settings.EMAIL_REVIEW])
