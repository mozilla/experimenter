from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from slack_sdk.errors import SlackApiError

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.slack.notification import send_slack_notification


class TestSlackNotifications(TestCase):
    def setUp(self):
        self.experiment = NimbusExperimentFactory.create()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_success(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {"user": {"id": "U123456"}}
        mock_client.chat_postMessage.return_value = {"ok": True}

        action_text = NimbusConstants.SLACK_EMAIL_ACTIONS[
            NimbusExperiment.EmailType.EXPERIMENT_END
        ]
        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=action_text,
        )

        mock_client.users_lookupByEmail.assert_called_once_with(email="test@example.com")
        mock_client.chat_postMessage.assert_called_once()

        # Verify message format includes experiment URL
        call_args = mock_client.chat_postMessage.call_args
        message = call_args.kwargs["text"]
        self.assertIn(self.experiment.experiment_url, message)
        self.assertIn(self.experiment.name, message)
        self.assertIn(action_text, message)
        self.assertIn("<@U123456>", message)

    @override_settings(SLACK_AUTH_TOKEN=None)
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_no_token(self, mock_webclient):
        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=NimbusConstants.SLACK_EMAIL_ACTIONS[
                NimbusExperiment.EmailType.EXPERIMENT_END
            ],
        )

        mock_webclient.assert_not_called()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_user_not_found(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.side_effect = SlackApiError(
            message="User not found", response={"error": "users_not_found"}
        )
        mock_client.chat_postMessage.return_value = {"ok": True}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["nonexistent@example.com"],
            action_text=NimbusConstants.SLACK_EMAIL_ACTIONS[
                NimbusExperiment.EmailType.EXPERIMENT_END
            ],
        )

        mock_client.chat_postMessage.assert_called_once()
        # Should still send message even if user lookup fails
        call_args = mock_client.chat_postMessage.call_args
        message = call_args.kwargs["text"]
        self.assertIn(self.experiment.experiment_url, message)
        self.assertNotIn("<@", message)  # No user mentions since lookup failed

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_post_message_fails(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {"user": {"id": "U123456"}}
        mock_client.chat_postMessage.side_effect = SlackApiError(
            message="Channel not found", response={"error": "channel_not_found"}
        )

        # Should raise exception to allow Celery retry
        with self.assertRaises(SlackApiError):
            send_slack_notification(
                experiment_id=self.experiment.id,
                email_addresses=["test@example.com"],
                action_text=NimbusConstants.SLACK_EMAIL_ACTIONS[
                    NimbusExperiment.EmailType.EXPERIMENT_END
                ],
            )

        mock_client.chat_postMessage.assert_called_once()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_experiment_not_found(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client

        send_slack_notification(
            experiment_id=999999,  # Non-existent ID
            email_addresses=["test@example.com"],
            action_text=NimbusConstants.SLACK_EMAIL_ACTIONS[
                NimbusExperiment.EmailType.EXPERIMENT_END
            ],
        )

        # Should not call Slack API when experiment doesn't exist
        mock_client.chat_postMessage.assert_not_called()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_with_requesting_user(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.side_effect = [
            {"user": {"id": "U123456"}},  # requesting user
            {"user": {"id": "U789012"}},  # mentioned user
        ]
        mock_client.chat_postMessage.return_value = {"ok": True}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=NimbusConstants.SLACK_FORM_ACTIONS[
                NimbusConstants.SLACK_ACTION_LAUNCH_REQUEST
            ],
            requesting_user_email="requester@example.com",
        )

        # Should call users_lookupByEmail twice
        self.assertEqual(mock_client.users_lookupByEmail.call_count, 2)
        mock_client.chat_postMessage.assert_called_once()

        call_args = mock_client.chat_postMessage.call_args
        message = call_args.kwargs["text"]
        # format: @user action: Experiment Name @mentions
        self.assertIn("<@U123456>", message)  # requesting user
        self.assertIn(
            NimbusConstants.SLACK_FORM_ACTIONS[
                NimbusConstants.SLACK_ACTION_LAUNCH_REQUEST
            ],
            message,
        )
        self.assertIn("<@U789012>", message)  # mentioned user

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_requesting_user_not_found(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        # First call (requesting user) fails, second call (mentioned user) succeeds
        mock_client.users_lookupByEmail.side_effect = [
            SlackApiError(
                message="User not found", response={"error": "users_not_found"}
            ),
            {"user": {"id": "U789012"}},
        ]
        mock_client.chat_postMessage.return_value = {"ok": True}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=NimbusConstants.SLACK_FORM_ACTIONS[
                NimbusConstants.SLACK_ACTION_LAUNCH_REQUEST
            ],
            requesting_user_email="nonexistent@example.com",
        )

        mock_client.chat_postMessage.assert_called_once()

        # Verify message format without requesting user mention
        call_args = mock_client.chat_postMessage.call_args
        message = call_args.kwargs["text"]
        self.assertNotIn("<@U123456>", message)  # requesting user not found
        self.assertIn("<@U789012>", message)  # mentioned user still there

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_no_duplicate_mention(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        requesting_email = "requester@example.com"
        mock_client.users_lookupByEmail.side_effect = [
            {"user": {"id": "U123456"}},
            {"user": {"id": "U789012"}},
        ]
        mock_client.chat_postMessage.return_value = {"ok": True}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=[requesting_email, "other@example.com"],
            action_text=NimbusConstants.SLACK_FORM_ACTIONS[
                NimbusConstants.SLACK_ACTION_LAUNCH_REQUEST
            ],
            requesting_user_email=requesting_email,
        )

        self.assertEqual(mock_client.users_lookupByEmail.call_count, 2)
        mock_client.chat_postMessage.assert_called_once()

        call_args = mock_client.chat_postMessage.call_args
        message = call_args.kwargs["text"]
        mention_count = message.count("<@U123456>")
        self.assertEqual(
            mention_count, 1, "Requesting user should only be mentioned once"
        )
        self.assertIn("<@U123456>", message)
        self.assertIn("<@U789012>", message)
        self.assertIn(
            NimbusConstants.SLACK_FORM_ACTIONS[
                NimbusConstants.SLACK_ACTION_LAUNCH_REQUEST
            ],
            message,
        )

    @override_settings(
        SLACK_AUTH_TOKEN="test-token", SLACK_NIMBUS_CHANNEL="custom-channel"
    )
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_channel_setting(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {"user": {"id": "U123456"}}
        mock_client.chat_postMessage.return_value = {"ok": True}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=NimbusConstants.SLACK_EMAIL_ACTIONS[
                NimbusExperiment.EmailType.EXPERIMENT_END
            ],
        )

        call_args = mock_client.chat_postMessage.call_args
        self.assertEqual(call_args.kwargs["channel"], "custom-channel")
        self.assertEqual(call_args.kwargs["unfurl_links"], False)
        self.assertEqual(call_args.kwargs["unfurl_media"], False)

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_empty_email(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {"user": {"id": "U123456"}}
        mock_client.chat_postMessage.return_value = {"ok": True}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["", None, "test@example.com"],
            action_text=NimbusConstants.SLACK_EMAIL_ACTIONS[
                NimbusExperiment.EmailType.EXPERIMENT_END
            ],
        )

        mock_client.users_lookupByEmail.assert_called_once_with(email="test@example.com")
        mock_client.chat_postMessage.assert_called_once()
