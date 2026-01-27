import logging

import markus
from celery import shared_task

from experimenter.experiments.models import NimbusExperiment
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
        experiments = NimbusExperiment.objects.filter(
            status__in=[
                NimbusExperiment.Status.LIVE,
                NimbusExperiment.Status.COMPLETE,
            ]
        )

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

        # Check for analysis errors (daily, weekly, overall)
        check_analysis_errors.delay(experiment_id)

        # Check if results became ready (daily, weekly, overall)
        check_analysis_ready.delay(experiment_id)

    except NimbusExperiment.DoesNotExist:
        logger.error(f"Experiment {experiment_id} not found")
    except Exception as e:
        logger.exception(f"Error checking alerts for experiment {experiment_id}: {e}")
        raise


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    retry_jitter=True,
)
@metrics.timer_decorator("check_analysis_errors")
def check_analysis_errors(experiment_id):
    # TODO: Implement in next ticket
    pass


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    retry_jitter=True,
)
@metrics.timer_decorator("check_analysis_ready")
def check_analysis_ready(experiment_id):
    # TODO: Implement in next ticket
    pass
