import logging

from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from experimenter.experiments.models import NimbusExperiment

logger = logging.getLogger(__name__)


def _get_slack_client():
    if not settings.SLACK_AUTH_TOKEN:
        return None
    return WebClient(token=settings.SLACK_AUTH_TOKEN)


def _lookup_users(client, emails):
    user_ids = []
    for email in emails:
        if not email:
            continue
        try:
            response = client.users_lookupByEmail(email=email)
            user_id = response["user"]["id"]
            user_ids.append(user_id)
        except SlackApiError as e:
            logger.warning(f"Could not find Slack user for {email}: {e}")
            continue
    return user_ids


def _is_user_in_channel(client, user_id, channel):
    try:
        response = client.conversations_members(channel=channel)
        return user_id in response.get("members", [])
    except SlackApiError as e:
        logger.warning(f"Failed to check if user {user_id} is in channel {channel}: {e}")
        return False


def _send_dm_to_user(client, user_id, message, channel_message_link=None):
    try:
        conversation = client.conversations_open(users=[user_id])
        channel_id = conversation["channel"]["id"]

        # Add channel message link if provided
        dm_message = message
        if channel_message_link:
            dm_message = f"{message}\n\nView in channel: {channel_message_link}"

        client.chat_postMessage(
            channel=channel_id, text=dm_message, unfurl_links=False, unfurl_media=False
        )
        logger.info(f"DM sent to user {user_id}")
    except SlackApiError as e:
        logger.warning(f"Failed to send DM to user {user_id}: {e}")


def send_slack_notification(
    experiment_id,
    email_addresses,
    action_text,
    requesting_user_email=None,
):
    if not (client := _get_slack_client()):
        logger.info("Slack not configured, skipping notification")
        return

    try:
        experiment = NimbusExperiment.objects.get(id=experiment_id)
    except NimbusExperiment.DoesNotExist:
        logger.error(f"Experiment {experiment_id} not found")
        return

    channel = settings.SLACK_NIMBUS_CHANNEL

    all_user_ids = []

    requesting_user_ids = []
    if requesting_user_email:
        requesting_user_ids = _lookup_users(client, [requesting_user_email])
        all_user_ids.extend(requesting_user_ids)
        # Exclude requesting_user_email from email_addresses to avoid duplicate mentions
        email_addresses = [e for e in email_addresses if e and e != requesting_user_email]

    mentioned_user_ids = _lookup_users(client, email_addresses)
    all_user_ids.extend(mentioned_user_ids)

    requesting_user_mention = (
        f"<@{requesting_user_ids[0]}>" if requesting_user_ids else ""
    )
    mentions = " ".join(f"<@{user_id}>" for user_id in mentioned_user_ids)

    if requesting_user_mention:
        message = (
            f"{requesting_user_mention} {action_text}: "
            f"<{experiment.experiment_url}|{experiment.name}>"
        )
    else:
        message = f"{action_text}: <{experiment.experiment_url}|{experiment.name}>"

    if mentions:
        message = f"{message} {mentions}"

    try:
        response = client.chat_postMessage(
            channel=channel, text=message, unfurl_links=False, unfurl_media=False
        )
        logger.info(f"Slack notification sent for experiment {experiment.name}")

        # Get the permalink to the channel message
        channel_message_link = None
        try:
            permalink_response = client.chat_getPermalink(
                channel=channel, message_ts=response["ts"]
            )
            channel_message_link = permalink_response["permalink"]
        except SlackApiError as e:
            logger.warning(f"Could not get permalink for channel message: {e}")

        for user_id in all_user_ids:
            if not _is_user_in_channel(client, user_id, channel):
                _send_dm_to_user(client, user_id, message, channel_message_link)
            else:
                logger.info(
                    f"Skipping DM to user {user_id} - already in channel {channel}"
                )

    except SlackApiError as e:
        logger.error(f"Failed to send Slack notification for {experiment.name}: {e}")
        raise
