import logging
from datetime import timedelta

import markus
from celery import shared_task
from django.utils import timezone

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusAlert, NimbusExperiment
from experimenter.slack.constants import SlackConstants
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

    Returns:
        Message timestamp for threading, or None if not sent.
    """
    metrics.incr("send_slack_notification.started")

    try:
        result = send_slack_notification(
            experiment_id=experiment_id,
            email_addresses=email_addresses,
            action_text=action_text,
            requesting_user_email=requesting_user_email,
        )

        logger.info(
            SlackConstants.SLACK_LOG_NOTIFICATION_TASK_SENT.format(
                experiment_id=experiment_id
            )
        )
        metrics.incr("send_slack_notification.completed")
        return result
    except Exception as e:
        metrics.incr("send_slack_notification.failed")
        msg = SlackConstants.SLACK_LOG_NOTIFICATION_TASK_FAILED.format(
            experiment_id=experiment_id
        )
        logger.error(f"{msg}: {e}")
        raise e


@shared_task
@metrics.timer_decorator("check_experiment_alerts")
def check_experiment_alerts():
    metrics.incr("check_experiment_alerts.started")

    try:
        # Get the cutoff date for COMPLETE experiments (3 days ago)
        three_days_ago = (timezone.now() - timedelta(days=3)).date()
        live_experiments = NimbusExperiment.objects.filter(
            status=NimbusExperiment.Status.LIVE
        )
        recent_complete_experiments = NimbusExperiment.objects.filter(
            status=NimbusExperiment.Status.COMPLETE,
            _computed_end_date__gte=three_days_ago,
        )
        experiments = live_experiments | recent_complete_experiments

        experiment_count = experiments.count()
        logger.info(
            SlackConstants.SLACK_LOG_CHECKING_ALERTS.format(count=experiment_count)
        )

        for experiment in experiments:
            check_single_experiment_alerts.delay(experiment.id)

        metrics.incr("check_experiment_alerts.completed")
        logger.info(
            SlackConstants.SLACK_LOG_ALERTS_SPAWNED.format(count=experiment_count)
        )

    except Exception as e:
        metrics.incr("check_experiment_alerts.failed")
        logger.error(f"{SlackConstants.SLACK_LOG_ERROR_CHECKING_ALERTS}: {e}")
        raise


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    retry_jitter=True,
)
@metrics.timer_decorator("check_single_experiment_alerts")
def check_single_experiment_alerts(experiment_id):
    try:
        experiment = NimbusExperiment.objects.get(id=experiment_id)
        logger.debug(
            SlackConstants.SLACK_LOG_CHECKING_EXPERIMENT.format(
                experiment=experiment.slug
            )
        )

        # Check if results became available
        _check_results_ready(experiment)

        # Check for analysis errors
        _check_analysis_errors(experiment)

    except NimbusExperiment.DoesNotExist:
        logger.error(
            SlackConstants.SLACK_LOG_EXPERIMENT_NOT_FOUND.format(
                experiment_id=experiment_id
            )
        )
    except Exception as e:
        msg = SlackConstants.SLACK_LOG_ERROR_CHECKING_EXPERIMENT.format(
            experiment_id=experiment_id
        )
        logger.exception(f"{msg}: {e}")
        raise


def _check_results_ready(experiment):
    for window, alert_type in NimbusConstants.ANALYSIS_WINDOW_TO_ALERT_TYPE.items():
        # Skip if we already sent this alert
        if NimbusAlert.objects.filter(
            experiment=experiment, alert_type=alert_type
        ).exists():
            continue

        # Check if results exist for this window
        if experiment.has_results_for_window(window):
            _send_results_ready_alert(experiment, window, alert_type)


def _send_results_ready_alert(experiment, window, alert_type):
    try:
        email_addresses = [experiment.owner.email] if experiment.owner else []
        message = SlackConstants.SLACK_RESULTS_READY_MESSAGE.format(
            window=window.capitalize()
        )
        result = send_slack_notification(
            experiment_id=experiment.id,
            email_addresses=email_addresses,
            action_text=message,
        )

        # Create alert record to prevent duplicates
        alert_kwargs = {
            "experiment": experiment,
            "alert_type": alert_type,
            "message": message,
        }
        if result:
            message_ts, channel_id = result
            alert_kwargs["slack_thread_id"] = message_ts
            alert_kwargs["slack_channel_id"] = channel_id

        NimbusAlert.objects.create(**alert_kwargs)

        logger.info(
            SlackConstants.SLACK_LOG_RESULTS_READY_SENT.format(
                window=window, experiment=experiment.slug
            )
        )
        metrics.incr(f"results_ready_alert.{window}.sent")

    except Exception as e:
        msg = SlackConstants.SLACK_LOG_FAILED_SEND_RESULTS_ALERT.format(
            window=window, experiment=experiment.slug
        )
        logger.error(f"{msg}: {e}")
        metrics.incr(f"results_ready_alert.{window}.failed")
        raise


def _extract_error_keys_from_message(message):
    return {
        line.lstrip("- ").replace(": ", "|")
        for line in message.split("\n")
        if ": " in line
    }


def _check_analysis_errors(experiment):
    if not experiment.results_data:
        return

    errors = experiment.results_data.get("v3", {}).get("errors", {})
    if not errors:
        return

    # Build list of current errors with unique keys
    error_items = []
    current_error_keys = set()

    for error_source, error_list in errors.items():
        if not error_list:
            continue

        first_error = error_list[0]
        exception_type = first_error.get("exception_type")
        if not exception_type:
            continue

        # Skip ignorable error types
        if exception_type in NimbusConstants.IGNORABLE_ANALYSIS_ERROR_TYPES:
            continue

        error_key = f"{error_source}|{exception_type}"
        current_error_keys.add(error_key)
        error_items.append(
            {
                "source": error_source,
                "type": exception_type,
                "message": first_error.get("message"),
            }
        )

    if not error_items:
        return

    # Get previous alert (if exists)
    previous_alert = NimbusAlert.objects.filter(
        experiment=experiment,
        alert_type=NimbusConstants.AlertType.ANALYSIS_ERROR,
    ).first()

    # Skip if errors haven't changed
    if previous_alert:
        previous_error_keys = _extract_error_keys_from_message(previous_alert.message)
        if current_error_keys == previous_error_keys:
            return

    # New/different errors detected! Send alert
    _send_error_alert(experiment, error_items)


def _send_error_alert(experiment, error_items):
    try:
        email_addresses = [experiment.owner.email] if experiment.owner else []

        error_lines = "\n".join(
            [f"- {item['source']}: {item['type']}" for item in error_items]
        )
        message = SlackConstants.SLACK_ANALYSIS_ERRORS_MESSAGE.format(
            error_lines=error_lines
        )

        result = send_slack_notification(
            experiment_id=experiment.id,
            email_addresses=email_addresses,
            action_text=message,
        )

        # Update or create alert record - keeps only one alert per experiment
        alert_defaults = {"message": message}
        if result:
            message_ts, channel_id = result
            alert_defaults["slack_thread_id"] = message_ts
            alert_defaults["slack_channel_id"] = channel_id

        NimbusAlert.objects.update_or_create(
            experiment=experiment,
            alert_type=NimbusConstants.AlertType.ANALYSIS_ERROR,
            defaults=alert_defaults,
        )

        logger.info(
            SlackConstants.SLACK_LOG_ANALYSIS_ERROR_SENT.format(
                experiment=experiment.slug
            )
        )
        metrics.incr("analysis_error_alert.sent")

    except Exception as e:
        msg = SlackConstants.SLACK_LOG_FAILED_SEND_ERROR_ALERT.format(
            experiment=experiment.slug
        )
        logger.error(f"{msg}: {e}")
        metrics.incr("analysis_error_alert.failed")
        raise
