from django.test import TestCase
from django.conf import settings

from experimenter.experiments.email import send_review_email
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.tests.mixins import MockMailMixin


class TestSendReviewEmail(MockMailMixin, TestCase):

    def test_send_review_email_without_needs_attention(self):
        experiment = ExperimentFactory.create(
            name="Experiment", slug="experiment"
        )
        send_review_email(experiment.name, experiment.experiment_url, False)
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
        send_review_email(experiment.name, experiment.experiment_url, True)
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
