import logging
from datetime import timedelta

import markus
from celery import shared_task
from django.utils import timezone

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusAlert, NimbusExperiment
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
        logger.info(f"Checking {experiment_count} experiments for alerts")

        for experiment in experiments:
            check_single_experiment_alerts.delay(experiment.id)

        metrics.incr("check_experiment_alerts.completed")
        logger.info(f"Spawned {experiment_count} alert check tasks")

    except Exception as e:
        metrics.incr("check_experiment_alerts.failed")
        logger.error(f"Error in check_experiment_alerts: {e}")
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
        logger.debug(f"Checking alerts for experiment: {experiment.slug}")

        # Check if results became available
        _check_results_ready(experiment)

        # Check for analysis errors
        _check_analysis_errors(experiment)

    except NimbusExperiment.DoesNotExist:
        logger.error(f"Experiment {experiment_id} not found")
    except Exception as e:
        logger.exception(f"Error checking alerts for experiment {experiment_id}: {e}")
        raise


def _check_results_ready(experiment):
    windows = [
        NimbusConstants.AnalysisWindow.WEEKLY,
        NimbusConstants.AnalysisWindow.OVERALL,
    ]

    for window in windows:
        alert_type = (
            NimbusConstants.AlertType.ANALYSIS_READY_WEEKLY
            if window == NimbusConstants.AnalysisWindow.WEEKLY
            else NimbusConstants.AlertType.ANALYSIS_READY_OVERALL
        )

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
        message = f"{window.capitalize()} analysis results are now available"
        send_slack_notification(
            experiment_id=experiment.id,
            email_addresses=email_addresses,
            action_text=message,
        )

        # Create alert record to prevent duplicates
        NimbusAlert.objects.create(
            experiment=experiment, alert_type=alert_type, message=message
        )

        logger.info(f"Sent {window} results ready alert for experiment {experiment.slug}")
        metrics.incr(f"results_ready_alert.{window}.sent")

    except Exception as e:
        logger.error(
            f"Failed to send {window} results alert for experiment {experiment.slug}: {e}"
        )
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
        message = f"Analysis errors detected:\n{error_lines}"

        send_slack_notification(
            experiment_id=experiment.id,
            email_addresses=email_addresses,
            action_text=message,
        )

        # Update or create alert record - keeps only one alert per experiment
        NimbusAlert.objects.update_or_create(
            experiment=experiment,
            alert_type=NimbusConstants.AlertType.ANALYSIS_ERROR,
            defaults={"message": message},
        )

        logger.info(f"Sent analysis error alert for {experiment.slug}")
        metrics.incr("analysis_error_alert.sent")

    except Exception as e:
        logger.error(f"Failed to send error alert for {experiment.slug}: {e}")
        metrics.incr("analysis_error_alert.failed")
        raise
