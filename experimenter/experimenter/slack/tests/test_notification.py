from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from slack_sdk.errors import SlackApiError

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusAlert, NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.slack.notification import (
    add_eyes_emoji_to_launch_message,
    send_experiment_launch_success_message,
    send_slack_notification,
)


class TestSlackNotifications(TestCase):
    def setUp(self):
        self.experiment = NimbusExperimentFactory.create()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_success(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {"user": {"id": "U123456"}}
        mock_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_client.chat_getPermalink.return_value = {
            "ok": True,
            "permalink": "https://mozilla.slack.com/archives/C123/p1234567890123456",
        }
        mock_client.conversations_open.return_value = {"channel": {"id": "D123456"}}
        # User is not in channel, so DM should be sent
        mock_client.conversations_members.return_value = {"members": []}

        action_text = NimbusConstants.SLACK_EMAIL_ACTIONS[
            NimbusExperiment.EmailType.EXPERIMENT_END
        ]
        result = send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=action_text,
        )

        self.assertEqual(result, ("1234567890.123456", "C123456"))

        mock_client.users_lookupByEmail.assert_called_once_with(email="test@example.com")
        # Should be called once for channel message and once for DM
        self.assertEqual(mock_client.chat_postMessage.call_count, 2)
        mock_client.chat_getPermalink.assert_called_once()
        mock_client.conversations_open.assert_called_once()

        # Verify channel message format includes experiment URL
        channel_call = mock_client.chat_postMessage.call_args_list[0]
        message = channel_call.kwargs["text"]
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
        mock_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_client.chat_getPermalink.return_value = {
            "ok": True,
            "permalink": "https://mozilla.slack.com/archives/C123/p1234567890123456",
        }

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

    @override_settings(SLACK_AUTH_TOKEN="test-token", SLACK_NIMBUS_CHANNEL="test-channel")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_with_requesting_user(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.side_effect = [
            {"user": {"id": "U123456"}},  # requesting user
            {"user": {"id": "U789012"}},  # mentioned user
        ]
        mock_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_client.chat_getPermalink.return_value = {
            "ok": True,
            "permalink": "https://mozilla.slack.com/archives/C123/p1234567890123456",
        }
        mock_client.conversations_open.return_value = {"channel": {"id": "D123456"}}
        # Neither user is in channel, so both should receive DMs
        mock_client.conversations_members.return_value = {"members": []}

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
        # Should be called once for channel message and twice for DMs
        self.assertEqual(mock_client.chat_postMessage.call_count, 3)
        mock_client.chat_getPermalink.assert_called_once()
        self.assertEqual(mock_client.conversations_open.call_count, 2)

        call_args = mock_client.chat_postMessage.call_args_list[0]
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

        # Verify both DM messages include channel name prefix
        dm_call_1 = mock_client.chat_postMessage.call_args_list[1]
        dm_call_2 = mock_client.chat_postMessage.call_args_list[2]
        for dm_call in [dm_call_1, dm_call_2]:
            dm_message = dm_call.kwargs["text"]
            self.assertIn("Join test-channel to get slack notifications:", dm_message)

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
        mock_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_client.chat_getPermalink.return_value = {
            "ok": True,
            "permalink": "https://mozilla.slack.com/archives/C123/p1234567890123456",
        }
        mock_client.conversations_open.return_value = {"channel": {"id": "D123456"}}
        # User is not in channel, so DM should be sent
        mock_client.conversations_members.return_value = {"members": []}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=NimbusConstants.SLACK_FORM_ACTIONS[
                NimbusConstants.SLACK_ACTION_LAUNCH_REQUEST
            ],
            requesting_user_email="nonexistent@example.com",
        )

        # Should be called once for channel message and once for DM to mentioned user
        self.assertEqual(mock_client.chat_postMessage.call_count, 2)

        # Verify channel message format without requesting user mention
        call_args = mock_client.chat_postMessage.call_args_list[0]
        message = call_args.kwargs["text"]
        self.assertIn("<@U789012>", message)  # mentioned user should be present
        self.assertNotIn("<@U123456>", message)  # requesting user should not be present

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
        mock_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_client.chat_getPermalink.return_value = {
            "ok": True,
            "permalink": "https://mozilla.slack.com/archives/C123/p1234567890123456",
        }
        mock_client.conversations_open.return_value = {"channel": {"id": "D123456"}}
        # Neither user is in channel, so both should receive DMs
        mock_client.conversations_members.return_value = {"members": []}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=[requesting_email, "other@example.com"],
            action_text=NimbusConstants.SLACK_FORM_ACTIONS[
                NimbusConstants.SLACK_ACTION_LAUNCH_REQUEST
            ],
            requesting_user_email=requesting_email,
        )

        self.assertEqual(mock_client.users_lookupByEmail.call_count, 2)
        # Should be called once for channel message and twice for DMs
        self.assertEqual(mock_client.chat_postMessage.call_count, 3)
        mock_client.chat_getPermalink.assert_called_once()
        self.assertEqual(mock_client.conversations_open.call_count, 2)

        call_args = mock_client.chat_postMessage.call_args_list[0]
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
        mock_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_client.chat_getPermalink.return_value = {
            "ok": True,
            "permalink": "https://mozilla.slack.com/archives/C123/p1234567890123456",
        }
        mock_client.conversations_open.return_value = {"channel": {"id": "D123456"}}
        # User is not in channel, so DM should be sent
        mock_client.conversations_members.return_value = {"members": []}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=NimbusConstants.SLACK_EMAIL_ACTIONS[
                NimbusExperiment.EmailType.EXPERIMENT_END
            ],
        )

        call_args = mock_client.chat_postMessage.call_args_list[0]
        self.assertEqual(call_args.kwargs["channel"], "custom-channel")
        self.assertEqual(call_args.kwargs["unfurl_links"], False)
        self.assertEqual(call_args.kwargs["unfurl_media"], False)

        # Verify DM message includes the custom channel name
        dm_call = mock_client.chat_postMessage.call_args_list[1]
        dm_message = dm_call.kwargs["text"]
        self.assertIn("Join custom-channel to get slack notifications:", dm_message)

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_empty_email(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {"user": {"id": "U123456"}}
        mock_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_client.chat_getPermalink.return_value = {
            "ok": True,
            "permalink": "https://mozilla.slack.com/archives/C123/p1234567890123456",
        }
        mock_client.conversations_open.return_value = {"channel": {"id": "D123456"}}
        # User is not in channel, so DM should be sent
        mock_client.conversations_members.return_value = {"members": []}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["", None, "test@example.com"],
            action_text=NimbusConstants.SLACK_EMAIL_ACTIONS[
                NimbusExperiment.EmailType.EXPERIMENT_END
            ],
        )

        mock_client.users_lookupByEmail.assert_called_once_with(email="test@example.com")
        # Should be called once for channel message and once for DM
        self.assertEqual(mock_client.chat_postMessage.call_count, 2)
        mock_client.chat_getPermalink.assert_called_once()
        mock_client.conversations_open.assert_called_once()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_dm_fails(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {"user": {"id": "U123456"}}
        mock_client.chat_postMessage.side_effect = [
            {"ok": True, "ts": "1234567890.123456", "channel": "C123456"},
            SlackApiError(
                message="DM failed", response={"error": "channel_not_found"}
            ),  # DM fails
        ]
        mock_client.chat_getPermalink.return_value = {
            "ok": True,
            "permalink": "https://mozilla.slack.com/archives/C123/p1234567890123456",
        }
        mock_client.conversations_open.return_value = {"channel": {"id": "D123456"}}
        # User is not in channel, so DM should be attempted
        mock_client.conversations_members.return_value = {"members": []}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=NimbusConstants.SLACK_EMAIL_ACTIONS[
                NimbusExperiment.EmailType.EXPERIMENT_END
            ],
        )

        # Should call chat_postMessage twice (channel + DM attempt)
        self.assertEqual(mock_client.chat_postMessage.call_count, 2)
        mock_client.conversations_open.assert_called_once()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_permalink_fails(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {"user": {"id": "U123456"}}
        mock_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_client.chat_getPermalink.side_effect = SlackApiError(
            message="Permalink failed", response={"error": "not_found"}
        )
        mock_client.conversations_open.return_value = {"channel": {"id": "D123456"}}
        # User is not in channel, so DM should be sent
        mock_client.conversations_members.return_value = {"members": []}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=NimbusConstants.SLACK_EMAIL_ACTIONS[
                NimbusExperiment.EmailType.EXPERIMENT_END
            ],
        )

        # Should still send DM even if permalink fails
        self.assertEqual(mock_client.chat_postMessage.call_count, 2)
        mock_client.conversations_open.assert_called_once()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_user_in_channel_no_dm(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {"user": {"id": "U123456"}}
        mock_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_client.chat_getPermalink.return_value = {
            "ok": True,
            "permalink": "https://mozilla.slack.com/archives/C123/p1234567890123456",
        }
        # User is in channel, so DM should NOT be sent
        mock_client.conversations_members.return_value = {"members": ["U123456"]}

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=NimbusConstants.SLACK_EMAIL_ACTIONS[
                NimbusExperiment.EmailType.EXPERIMENT_END
            ],
        )

        mock_client.users_lookupByEmail.assert_called_once_with(email="test@example.com")
        # Should only be called once for channel message (no DM)
        self.assertEqual(mock_client.chat_postMessage.call_count, 1)
        mock_client.chat_getPermalink.assert_called_once()
        # conversations_open should not be called since no DM is sent
        mock_client.conversations_open.assert_not_called()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_mixed_channel_membership(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.side_effect = [
            {"user": {"id": "U123456"}},  # requesting user
            {"user": {"id": "U789012"}},  # mentioned user
        ]
        mock_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_client.chat_getPermalink.return_value = {
            "ok": True,
            "permalink": "https://mozilla.slack.com/archives/C123/p1234567890123456",
        }
        mock_client.conversations_open.return_value = {"channel": {"id": "D123456"}}
        # Requesting user (U123456) is in channel, mentioned user (U789012) is not
        mock_client.conversations_members.return_value = {
            "members": ["U123456", "U999999"]
        }

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=NimbusConstants.SLACK_FORM_ACTIONS[
                NimbusConstants.SLACK_ACTION_LAUNCH_REQUEST
            ],
            requesting_user_email="requester@example.com",
        )

        self.assertEqual(mock_client.users_lookupByEmail.call_count, 2)
        # Should be called once for channel message and once for DM to U789012 only
        self.assertEqual(mock_client.chat_postMessage.call_count, 2)
        mock_client.chat_getPermalink.assert_called_once()
        # Only one DM should be sent (to U789012)
        self.assertEqual(mock_client.conversations_open.call_count, 1)

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_slack_notification_channel_check_fails(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {"user": {"id": "U123456"}}
        mock_client.chat_postMessage.return_value = {
            "ok": True,
            "ts": "1234567890.123456",
            "channel": "C123456",
        }
        mock_client.chat_getPermalink.return_value = {
            "ok": True,
            "permalink": "https://mozilla.slack.com/archives/C123/p1234567890123456",
        }
        mock_client.conversations_open.return_value = {"channel": {"id": "D123456"}}
        mock_client.conversations_members.side_effect = SlackApiError(
            message="Error", response={"error": "channel_not_found"}
        )

        send_slack_notification(
            experiment_id=self.experiment.id,
            email_addresses=["test@example.com"],
            action_text=NimbusConstants.SLACK_EMAIL_ACTIONS[
                NimbusExperiment.EmailType.EXPERIMENT_END
            ],
        )

        # Should be called once for channel message and once for DM
        # (DM is sent when we can't determine membership)
        self.assertEqual(mock_client.chat_postMessage.call_count, 2)
        mock_client.conversations_open.assert_called_once()

    @override_settings(
        SLACK_AUTH_TOKEN="test-token",
        SLACK_NIMBUS_CHANNEL="C123456",
    )
    @patch("experimenter.slack.notification.WebClient")
    def test_send_experiment_launch_success_message(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.chat_postMessage.return_value = {"ok": True, "channel": "C123456"}
        mock_client.reactions_add.return_value = {"ok": True}

        thread_ts = "1234567890.123456"
        result = send_experiment_launch_success_message(
            experiment_id=self.experiment.id,
            thread_ts=thread_ts,
        )

        self.assertTrue(result)
        # Verify threaded message was posted
        mock_client.chat_postMessage.assert_called_once()
        call_args = mock_client.chat_postMessage.call_args
        self.assertIn("✅", call_args.kwargs["text"])
        self.assertIn("is now LIVE", call_args.kwargs["text"])
        self.assertIn(self.experiment.name, call_args.kwargs["text"])
        self.assertIn(self.experiment.slug, call_args.kwargs["text"])
        self.assertEqual(call_args.kwargs["thread_ts"], thread_ts)

        # Verify reaction emoji was added with the correct channel ID
        mock_client.reactions_add.assert_called_once()
        reaction_call = mock_client.reactions_add.call_args
        self.assertEqual(reaction_call.kwargs["channel"], "C123456")
        self.assertEqual(reaction_call.kwargs["name"], "white_check_mark")
        self.assertEqual(reaction_call.kwargs["timestamp"], thread_ts)

    @override_settings(
        SLACK_AUTH_TOKEN="test-token",
        SLACK_NIMBUS_CHANNEL="C123456",
    )
    @patch("experimenter.slack.notification.WebClient")
    def test_send_experiment_launch_success_message_slack_error(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.chat_postMessage.side_effect = SlackApiError(
            message="Slack error", response={"error": "channel_not_found"}
        )

        thread_ts = "1234567890.123456"
        result = send_experiment_launch_success_message(
            experiment_id=self.experiment.id,
            thread_ts=thread_ts,
        )

        self.assertFalse(result)
        mock_client.chat_postMessage.assert_called_once()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_send_experiment_launch_success_message_not_found(self, mock_webclient):
        thread_ts = "1234567890.123456"
        result = send_experiment_launch_success_message(
            experiment_id=999999,
            thread_ts=thread_ts,
        )

        self.assertFalse(result)
        mock_webclient.assert_called_once()

    @override_settings(SLACK_AUTH_TOKEN=None)
    def test_send_experiment_launch_success_message_no_token(self):
        thread_ts = "1234567890.123456"
        result = send_experiment_launch_success_message(
            experiment_id=self.experiment.id,
            thread_ts=thread_ts,
        )

        self.assertFalse(result)

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_add_eyes_emoji_to_launch_message_success(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.reactions_add.return_value = {"ok": True}

        NimbusAlert.objects.create(
            experiment=self.experiment,
            alert_type=NimbusConstants.AlertType.LAUNCH_REQUEST,
            message="Test launch request",
            slack_thread_id="1234567890.123456",
            slack_channel_id="C123456",
        )

        result = add_eyes_emoji_to_launch_message(
            self.experiment, NimbusConstants.AlertType.LAUNCH_REQUEST
        )

        self.assertTrue(result)
        mock_client.reactions_add.assert_called_once()
        call_args = mock_client.reactions_add.call_args
        self.assertEqual(call_args.kwargs["channel"], "C123456")
        self.assertEqual(call_args.kwargs["name"], "eyes")
        self.assertEqual(call_args.kwargs["timestamp"], "1234567890.123456")

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_add_eyes_emoji_to_launch_message_no_alert(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client

        # Don't create any alert
        result = add_eyes_emoji_to_launch_message(
            self.experiment, NimbusConstants.AlertType.LAUNCH_REQUEST
        )

        self.assertFalse(result)
        # Should not call Slack API
        mock_client.reactions_add.assert_not_called()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_add_eyes_emoji_to_launch_message_no_thread_id(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client

        # Create alert without slack_thread_id
        NimbusAlert.objects.create(
            experiment=self.experiment,
            alert_type=NimbusConstants.AlertType.LAUNCH_REQUEST,
            message="Test launch request",
            slack_thread_id=None,
        )

        result = add_eyes_emoji_to_launch_message(
            self.experiment, NimbusConstants.AlertType.LAUNCH_REQUEST
        )

        self.assertFalse(result)
        # Should not call Slack API
        mock_client.reactions_add.assert_not_called()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_add_eyes_emoji_to_launch_message_no_channel_id(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client

        # Create alert without slack_channel_id
        NimbusAlert.objects.create(
            experiment=self.experiment,
            alert_type=NimbusConstants.AlertType.LAUNCH_REQUEST,
            message="Test launch request",
            slack_thread_id="1234567890.123456",
            slack_channel_id=None,
        )

        result = add_eyes_emoji_to_launch_message(
            self.experiment, NimbusConstants.AlertType.LAUNCH_REQUEST
        )

        self.assertFalse(result)
        # Should not call Slack API
        mock_client.reactions_add.assert_not_called()

    @override_settings(SLACK_AUTH_TOKEN="test-token")
    @patch("experimenter.slack.notification.WebClient")
    def test_add_eyes_emoji_to_launch_message_slack_error(self, mock_webclient):
        mock_client = Mock()
        mock_webclient.return_value = mock_client
        mock_client.reactions_add.side_effect = SlackApiError(
            message="Slack error", response={"error": "channel_not_found"}
        )

        NimbusAlert.objects.create(
            experiment=self.experiment,
            alert_type=NimbusConstants.AlertType.LAUNCH_REQUEST,
            message="Test launch request",
            slack_thread_id="1234567890.123456",
            slack_channel_id="C123456",
        )

        result = add_eyes_emoji_to_launch_message(
            self.experiment, NimbusConstants.AlertType.LAUNCH_REQUEST
        )

        self.assertFalse(result)
        mock_client.reactions_add.assert_called_once()
