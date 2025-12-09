from unittest import mock

from django.test import TestCase

from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.slack import tasks


class TestNimbusSendSlackNotification(TestCase):
    @mock.patch("experimenter.slack.tasks.send_slack_notification")
    def test_sends_slack_notification_successfully(self, mock_send_slack):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        email_addresses = ["user1@example.com", "user2@example.com"]
        action_text = "requests launch"
        requesting_user_email = "requester@example.com"

        tasks.nimbus_send_slack_notification(
            experiment.id,
            email_addresses,
            action_text,
            requesting_user_email,
        )

        mock_send_slack.assert_called_once_with(
            experiment_id=experiment.id,
            email_addresses=email_addresses,
            action_text=action_text,
            requesting_user_email=requesting_user_email,
        )

    @mock.patch("experimenter.slack.tasks.send_slack_notification")
    def test_sends_slack_notification_without_requesting_user(self, mock_send_slack):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        email_addresses = ["user1@example.com"]
        action_text = "ready to end"

        tasks.nimbus_send_slack_notification(
            experiment.id,
            email_addresses,
            action_text,
        )

        mock_send_slack.assert_called_once_with(
            experiment_id=experiment.id,
            email_addresses=email_addresses,
            action_text=action_text,
            requesting_user_email=None,
        )

    @mock.patch("experimenter.slack.tasks.send_slack_notification")
    def test_slack_notification_reraises_exception(self, mock_send_slack):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        email_addresses = ["user1@example.com"]
        action_text = "requests launch"

        mock_send_slack.side_effect = Exception("Slack API error")

        with self.assertRaises(Exception) as context:
            tasks.nimbus_send_slack_notification(
                experiment.id,
                email_addresses,
                action_text,
            )

        self.assertIn("Slack API error", str(context.exception))
