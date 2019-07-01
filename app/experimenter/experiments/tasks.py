import markus
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from celery.utils.log import get_task_logger

from experimenter.celery import app
from experimenter.experiments import bugzilla, normandy, email
from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.models import Experiment, ExperimentEmail
from experimenter.notifications.models import Notification
from datetime import date, timedelta


logger = get_task_logger(__name__)
metrics = markus.get_metrics("experiments.tasks")


NOTIFICATION_MESSAGE_CREATE_BUG = (
    'A <a target="_blank" rel="noreferrer noopener" href="{bug_url}">Bugzilla '
    "Ticket</a> was created for your experiment"
)
NOTIFICATION_MESSAGE_CREATE_BUG_FAILED = (
    "Experimenter failed to create a Bugzilla Ticket "
    "for your experiment.  Please contact an Experimenter "
    "Administrator on #ask-experimenter on Slack."
)
NOTIFICATION_MESSAGE_UPDATE_BUG = (
    'The <a target="_blank" rel="noreferrer noopener" href="{bug_url}">'
    "Ticket</a> was updated with the details "
    "of this experiment"
)
NOTIFICATION_MESSAGE_UPDATE_BUG_FAILED = (
    "Experimenter failed to update the Bugzilla Ticket "
    "for your experiment.  Please contact an Experimenter "
    "Administrator on #ask-experimenter on Slack."
)

STATUS_UPDATE_MAPPING = {
    Experiment.STATUS_ACCEPTED: Experiment.STATUS_LIVE,
    Experiment.STATUS_LIVE: Experiment.STATUS_COMPLETE,
}
NOTIFICATION_MESSAGE_ARCHIVE_COMMENT = (
    'The <a target="_blank" rel="noreferrer noopener" href="{bug_url}">'
    "Ticket</a> has updated its resolution and status"
)

NOTIFICATION_MESSAGE_ARCHIVE_ERROR_MESSAGE = (
    'The <a target="_blank" rel="noreferrer noopener" href="{bug_url}">'
    "Ticket</a> was UNABLE to update its resolution and status"
)


@app.task
@metrics.timer_decorator("create_experiment_bug.timing")
def create_experiment_bug_task(user_id, experiment_id):
    metrics.incr("create_experiment_bug.started")

    experiment = Experiment.objects.get(id=experiment_id)

    logger.info("Creating Bugzilla ticket")
    try:
        bugzilla_id = bugzilla.create_experiment_bug(experiment)
        logger.info("Bugzilla ticket created")
        experiment.bugzilla_id = bugzilla_id
        experiment.save()

        Notification.objects.create(
            user_id=user_id,
            message=NOTIFICATION_MESSAGE_CREATE_BUG.format(
                bug_url=experiment.bugzilla_url
            ),
        )
        metrics.incr("create_experiment_bug.completed")
        logger.info("Bugzilla ticket notification sent")
    except bugzilla.BugzillaError as e:
        metrics.incr("create_experiment_bug.failed")
        logger.info("Bugzilla ticket creation failed")

        Notification.objects.create(
            user_id=user_id, message=NOTIFICATION_MESSAGE_CREATE_BUG_FAILED
        )
        logger.info("Bugzilla ticket notification sent")
        raise e


@app.task
@metrics.timer_decorator("update_experiment_bug.timing")
def update_experiment_bug_task(user_id, experiment_id):
    metrics.incr("update_experiment_bug.started")

    experiment = Experiment.objects.get(id=experiment_id)

    if experiment.risk_internal_only:
        logger.info("Skipping Bugzilla update for internal only experiment")
        return

    logger.info("Updating Bugzilla Ticket")

    try:
        bugzilla.update_experiment_bug(experiment)
        logger.info("Bugzilla Ticket updated")
        Notification.objects.create(
            user_id=user_id,
            message=NOTIFICATION_MESSAGE_UPDATE_BUG.format(
                bug_url=experiment.bugzilla_url
            ),
        )
        metrics.incr("update_experiment_bug.completed")
        logger.info("Bugzilla Update notification sent")
    except bugzilla.BugzillaError as e:
        Notification.objects.create(
            user_id=user_id, message=NOTIFICATION_MESSAGE_UPDATE_BUG_FAILED
        )
        metrics.incr("update_experiment_bug.failed")
        logger.info("Failed bugzilla update")
        raise e


@app.task
@metrics.timer_decorator("update_experiment_info.timing")
def update_experiment_info():
    metrics.incr("update_experiment_info.started")
    logger.info("Updating experiment info")
    launch_experiments = Experiment.objects.filter(
        Q(status=Experiment.STATUS_ACCEPTED) | Q(status=Experiment.STATUS_LIVE)
    )

    for experiment in launch_experiments:
        try:
            logger.info("Updating Experiment: {}".format(experiment))
            if experiment.normandy_id:
                update_status(experiment)
                send_experiment_ending_emails(experiment)
            else:
                logger.info(
                    "No Normandy ID found skipping: {}".format(experiment)
                )

        except (IntegrityError, KeyError, normandy.NormandyError):
            logger.info(
                "Failed to get Normandy Recipe. Recipe ID: {}".format(
                    experiment.normandy_id
                )
            )
            metrics.incr("update_experiment_info.failed")
    metrics.incr("update_experiment_info.completed")


def add_start_date_comment(experiment):
    comment = "Start Date: {} End Date: {}".format(
        experiment.start_date, experiment.end_date
    )
    bugzilla.add_experiment_comment(experiment, comment)


def update_status(experiment):
    recipe_data = normandy.get_recipe(experiment.normandy_id)
    if needs_to_be_updated(recipe_data, experiment.status):
        logger.info("Updating experiment Status")
        enabler_email = recipe_data["enabled_states"][0]["creator"]["email"]
        enabler, _ = get_user_model().objects.get_or_create(
            email=enabler_email
        )
        old_status = experiment.status
        new_status = STATUS_UPDATE_MAPPING[old_status]
        experiment.status = new_status
        with transaction.atomic():
            experiment.save()

            experiment.changes.create(
                changed_by=enabler,
                old_status=old_status,
                new_status=new_status,
            )
            metrics.incr("update_experiment_info.updated")
            logger.info("Finished updating Experiment: {}".format(experiment))

        if experiment.status == Experiment.STATUS_LIVE:
            add_start_date_comment(experiment)
            email.send_experiment_launch_email(experiment)
            logger.info(
                "Sent launch email for Experiment: {}".format(experiment)
            )

        if experiment.status == Experiment.STATUS_COMPLETE:
            bugzilla.update_bug_resolution(experiment)


def send_experiment_ending_emails(experiment):
    # send experiment ending soon emails if end date is 5 days out
    if experiment.end_date - date.today() <= timedelta(days=5):
        if not ExperimentEmail.objects.filter(
            experiment=experiment, type=ExperimentConstants.EXPERIMENT_ENDS
        ):
            email.send_experiment_ending_email(experiment)
            logger.info(
                "Sent ending email for Experiment: {}".format(experiment)
            )


def needs_to_be_updated(recipe_data, status):
    if recipe_data is None:
        return False
    enabled = recipe_data["enabled"]
    accepted_update = enabled and status == Experiment.STATUS_ACCEPTED
    live_update = not enabled and status == Experiment.STATUS_LIVE
    return accepted_update or live_update


@app.task
@metrics.timer_decorator("update_bug_resolution.timing")
def update_bug_resolution_task(user_id, experiment_id):
    metrics.incr("update_bug_resolution.started")
    experiment = Experiment.objects.get(id=experiment_id)

    if (
        experiment.status == experiment.STATUS_COMPLETE
        or experiment.bugzilla_id is None
    ):
        logger.info(
            "Skipping update either experiment complete or no bugzilla ticket"
        )
        return

    logger.info("Updating Bugzilla Resolution")

    try:
        bugzilla.update_bug_resolution(experiment)
        logger.info("Bugzilla resolution updated")
        Notification.objects.create(
            user_id=user_id,
            message=NOTIFICATION_MESSAGE_ARCHIVE_COMMENT.format(
                bug_url=experiment.bugzilla_url
            ),
        )
        metrics.incr("update_bug_resolution.completed")
        logger.info("Bugzilla resolution update sent")
    except bugzilla.BugzillaError as e:
        metrics.incr("update_bug_resolution.failed")
        logger.info("Failed to update resolution of bugzilla ticket")
        Notification.objects.create(
            user_id=user_id,
            message=NOTIFICATION_MESSAGE_ARCHIVE_ERROR_MESSAGE.format(
                bug_url=experiment.bugzilla_url
            ),
        )
        raise e
