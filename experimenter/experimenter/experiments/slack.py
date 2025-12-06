import logging

from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from experimenter.experiments.models import NimbusExperiment

logger = logging.getLogger(__name__)


def _get_slack_client():
    if not (token := getattr(settings, "SLACK_AUTH_TOKEN", None)):
        return None
    return WebClient(token=token)


def _get_user_mentions(client, emails):
    mentions = []
    for email in emails:
        if not email:
            continue
        try:
            response = client.users_lookupByEmail(email=email)
            mentions.append(f"<@{response['user']['id']}>")
        except SlackApiError as e:
            logger.warning(f"Could not find Slack user for {email}: {e}")
            continue
    return " ".join(mentions)


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

    channel = getattr(settings, "SLACK_NIMBUS_CHANNEL", "nimbus-notifications")

    requesting_user_mention = ""
    if requesting_user_email:
        requesting_user_mention = _get_user_mentions(client, [requesting_user_email])

    mentions = _get_user_mentions(client, email_addresses)

    if requesting_user_mention:
        message = (
            f"<Nimbus> {requesting_user_mention} "
            f"<{experiment.experiment_url}|{experiment.name}> {action_text}"
        )
    else:
        message = (
            f"<Nimbus> <{experiment.experiment_url}|{experiment.name}> {action_text}"
        )

    if mentions:
        message += f" {mentions}"

    try:
        client.chat_postMessage(
            channel=channel, text=message, unfurl_links=False, unfurl_media=False
        )
        logger.info(f"Slack notification sent for experiment {experiment.name}")
    except SlackApiError as e:
        logger.error(f"Failed to send Slack notification for {experiment.name}: {e}")
        raise
