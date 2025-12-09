import logging

import markus
from celery import shared_task

from experimenter.slack.notification import send_slack_notification

logger = logging.getLogger(__name__)
metrics = markus.get_metrics("slack.tasks")


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    retry_jitter=True,
)
@metrics.timer_decorator("send_slack_notification")
def nimbus_send_slack_notification(
    experiment_id,
    email_addresses,
    action_text,
    requesting_user_email=None,
):
    """
    An invoked task that sends a Slack notification for an experiment action.
    """
    metrics.incr("send_slack_notification.started")

    try:
        send_slack_notification(
            experiment_id=experiment_id,
            email_addresses=email_addresses,
            action_text=action_text,
            requesting_user_email=requesting_user_email,
        )

        logger.info(f"Slack notification sent for experiment {experiment_id}")
        metrics.incr("send_slack_notification.completed")
    except Exception as e:
        metrics.incr("send_slack_notification.failed")
        logger.error(
            f"Sending Slack notification for experiment {experiment_id} failed: {e}"
        )
        raise e
