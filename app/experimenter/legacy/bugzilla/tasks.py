import markus
from celery.utils.log import get_task_logger

from experimenter.celery import app
from experimenter.legacy.bugzilla import client as bugzilla
from experimenter.legacy.legacy_experiments.models import Experiment
from experimenter.notifications.models import Notification

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

    if experiment.risk_confidential:
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
@metrics.timer_decorator("comp_experiment_update_res_task.timing")
def comp_experiment_update_res_task(experiment_id):
    experiment = Experiment.objects.get(id=experiment_id)
    metrics.incr("comp_experiment_update_res_task.started")
    logger.info("Updating Bugzilla Resolution")
    try:
        bugzilla.update_bug_resolution(experiment)
        logger.info("Bugzilla Resolution Updated")
        metrics.incr("comp_experiment_update_res_task.completed")
    except bugzilla.BugzillaError as e:
        metrics.incr("comp_experiment_update_res_task.failed")
        logger.info("update bug resolution failed")
        raise e


@app.task
@metrics.timer_decorator("add_start_date_comment.timing")
def add_start_date_comment_task(experiment_id):
    experiment = Experiment.objects.get(id=experiment_id)
    metrics.incr("add_start_data_comment.started")
    logger.info("Adding Bugzilla Start Date Comment")
    comment = "Start Date: {} End Date: {}".format(
        experiment.start_date, experiment.end_date
    )
    try:
        bugzilla_id = experiment.bugzilla_id
        bugzilla.add_experiment_comment(bugzilla_id, comment)
        logger.info("Bugzilla Comment Added")
        metrics.incr("add_start_date_comment.completed")
    except bugzilla.BugzillaError as e:
        logger.info("Comment start date failed to be added")
        metrics.incr("add_start_date_comment.failed")
        raise e


@app.task
@metrics.timer_decorator("update_bug_resolution.timing")
def update_bug_resolution_task(user_id, experiment_id):
    metrics.incr("update_bug_resolution.started")
    experiment = Experiment.objects.get(id=experiment_id)

    if experiment.status == experiment.STATUS_COMPLETE or experiment.bugzilla_id is None:
        logger.info("Skipping update either experiment complete or no bugzilla ticket")
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
