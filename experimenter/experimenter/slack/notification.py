import logging

from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from experimenter.experiments.models import NimbusAlert, NimbusExperiment
from experimenter.slack.constants import SlackConstants

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
            msg = SlackConstants.SLACK_LOG_COULD_NOT_FIND_USER.format(email=email)
            logger.warning(f"{msg}: {e}")
            continue
    return user_ids


def _is_user_in_channel(client, user_id, channel):
    try:
        response = client.conversations_members(channel=channel)
        return user_id in response.get("members", [])
    except SlackApiError as e:
        msg = SlackConstants.SLACK_LOG_FAILED_CHECK_USER_IN_CHANNEL.format(
            user_id=user_id, channel=channel
        )
        logger.warning(f"{msg}: {e}")
        return False


def _send_dm_to_user(client, user_id, message, channel_message_link=None):
    try:
        conversation = client.conversations_open(users=[user_id])
        channel_id = conversation["channel"]["id"]

        # Add prefix message and channel message link if provided
        dm_message = SlackConstants.SLACK_DM_PREFIX.format(
            channel=settings.SLACK_NIMBUS_CHANNEL, message=message
        )
        if channel_message_link:
            link_suffix = SlackConstants.SLACK_DM_CHANNEL_LINK_SUFFIX.format(
                channel_message_link=channel_message_link
            )
            dm_message = f"{dm_message}{link_suffix}"

        client.chat_postMessage(
            channel=channel_id, text=dm_message, unfurl_links=False, unfurl_media=False
        )
        logger.info(SlackConstants.SLACK_LOG_DM_SENT.format(user_id=user_id))
    except SlackApiError as e:
        logger.warning(
            f"{SlackConstants.SLACK_LOG_FAILED_SEND_DM.format(user_id=user_id)}: {e}"
        )


def send_slack_notification(
    experiment_id,
    email_addresses,
    action_text,
    requesting_user_email=None,
):
    if not (client := _get_slack_client()):
        logger.info(
            SlackConstants.SLACK_LOG_NOT_CONFIGURED.format(operation="notification")
        )
        return None

    try:
        experiment = NimbusExperiment.objects.get(id=experiment_id)
    except NimbusExperiment.DoesNotExist:
        logger.error(
            SlackConstants.SLACK_LOG_EXPERIMENT_NOT_FOUND.format(
                experiment_id=experiment_id
            )
        )
        return None

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

    all_mentions = []
    if requesting_user_ids:
        all_mentions.extend(f"<@{user_id}>" for user_id in requesting_user_ids)
    if mentioned_user_ids:
        all_mentions.extend(f"<@{user_id}>" for user_id in mentioned_user_ids)

    message = f"{action_text}: <{experiment.experiment_url}|{experiment.name}>"
    if all_mentions:
        message = f"{message} @ {' '.join(all_mentions)}"

    try:
        response = client.chat_postMessage(
            channel=channel, text=message, unfurl_links=False, unfurl_media=False
        )
        message_ts = response["ts"]
        channel_id = response["channel"]
        logger.info(
            SlackConstants.SLACK_LOG_NOTIFICATION_SENT.format(experiment=experiment.name)
        )

        # Get the permalink to the channel message
        channel_message_link = None
        try:
            permalink_response = client.chat_getPermalink(
                channel=channel, message_ts=message_ts
            )
            channel_message_link = permalink_response["permalink"]
        except SlackApiError as e:
            logger.warning(f"{SlackConstants.SLACK_LOG_COULD_NOT_GET_PERMALINK}: {e}")

        for user_id in all_user_ids:
            if not _is_user_in_channel(client, user_id, channel):
                _send_dm_to_user(client, user_id, message, channel_message_link)
            else:
                logger.info(
                    SlackConstants.SLACK_LOG_USER_IN_CHANNEL.format(
                        user_id=user_id, channel=channel
                    )
                )

        return (message_ts, channel_id)

    except SlackApiError as e:
        msg = SlackConstants.SLACK_LOG_FAILED_SEND_NOTIFICATION.format(
            experiment=experiment.name
        )
        logger.error(f"{msg}: {e}")
        raise


def send_experiment_launch_success_message(experiment_id, thread_ts):
    if not (client := _get_slack_client()):
        logger.info(
            SlackConstants.SLACK_LOG_NOT_CONFIGURED.format(
                operation="launch success notification"
            )
        )
        return False

    try:
        experiment = NimbusExperiment.objects.get(id=experiment_id)
    except NimbusExperiment.DoesNotExist:
        logger.error(
            SlackConstants.SLACK_LOG_EXPERIMENT_NOT_FOUND.format(
                experiment_id=experiment_id
            )
        )
        return False

    channel = settings.SLACK_NIMBUS_CHANNEL

    message = SlackConstants.SLACK_LAUNCH_SUCCESS_MESSAGE.format(
        name=experiment.name,
        url=experiment.experiment_url,
        slug=experiment.slug,
    )

    try:
        # Send threaded reply to the original launch request
        post_response = client.chat_postMessage(
            channel=channel,
            text=message,
            thread_ts=thread_ts,
        )

        channel_id = post_response["channel"]

        # Add reaction emoji to original message
        client.reactions_add(
            channel=channel_id,
            name="white_check_mark",
            timestamp=thread_ts,
        )

        logger.info(
            SlackConstants.SLACK_LOG_LAUNCH_SUCCESS_SENT.format(
                experiment=experiment.slug
            )
        )
        return True

    except SlackApiError as e:
        msg = SlackConstants.SLACK_LOG_FAILED_SEND_LAUNCH_SUCCESS.format(
            experiment=experiment.slug
        )
        logger.error(f"{msg}: {e}")
        return False


def add_eyes_emoji_to_launch_message(experiment, alert_type):
    if not (client := _get_slack_client()):
        logger.info(
            SlackConstants.SLACK_LOG_NOT_CONFIGURED.format(
                operation="eyes emoji notification"
            )
        )
        return False

    try:
        alert = NimbusAlert.objects.filter(
            experiment=experiment,
            alert_type=alert_type,
            slack_thread_id__isnull=False,
        ).first()

        if not alert or not alert.slack_thread_id:
            logger.info(
                SlackConstants.SLACK_LOG_NO_SLACK_THREAD.format(
                    experiment=experiment.slug
                )
            )
            return False

        thread_ts = alert.slack_thread_id
        channel_id = alert.slack_channel_id

        if not channel_id:
            logger.error(SlackConstants.SLACK_LOG_NO_CHANNEL_ID.format(alert_id=alert.id))
            return False

        # Add eyes emoji reaction to the message
        client.reactions_add(
            channel=channel_id,
            name="eyes",
            timestamp=thread_ts,
        )

        logger.info(
            SlackConstants.SLACK_LOG_EYES_EMOJI_ADDED.format(experiment=experiment.slug)
        )
        return True

    except SlackApiError as e:
        msg = SlackConstants.SLACK_LOG_FAILED_ADD_EYES_EMOJI.format(
            experiment=experiment.slug
        )
        logger.error(f"{msg}: {e}")
        return False
