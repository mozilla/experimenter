import decimal

import markus
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.conf import settings
from celery.utils.log import get_task_logger

from experimenter import bugzilla
from experimenter import normandy
from experimenter.celery import app
from experimenter.experiments import email
from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.changelog_utils import update_experiment_with_change_log
from experimenter.experiments.models import Experiment, ExperimentEmail
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
@metrics.timer_decorator("update_experiment_info.timing")
def update_experiment_info():
    update_recipe_ids_to_experiments.delay()
    update_launched_experiments.delay()


@app.task
@metrics.timer_decorator("update_recipe_ids_to_experiments.timing")
def update_recipe_ids_to_experiments():
    metrics.incr("update_ready_to_ship_experiments.started")
    logger.info("Update Recipes to Experiments")

    ready_to_ship_experiments = Experiment.objects.filter(
        status__in=[Experiment.STATUS_SHIP, Experiment.STATUS_ACCEPTED]
    )
    for experiment in ready_to_ship_experiments:
        try:
            logger.info("Updating Experiment: {}".format(experiment))
            recipe_data = normandy.get_recipe_list(experiment.slug)

            if len(recipe_data):
                recipe_ids = [r["id"] for r in recipe_data]
                # sort to get oldest id to be primary
                recipe_ids.sort()
                changed_data = {
                    "normandy_id": recipe_ids[0],
                    "other_normandy_ids": recipe_ids[1:],
                    "status": Experiment.STATUS_ACCEPTED,
                }
                update_experiment_with_change_log(experiment, changed_data)

        except (IntegrityError, KeyError, normandy.NormandyError) as e:
            logger.info(f"Failed to update Experiment {experiment}: {e}")
            metrics.incr("update_ready_to_experiments.failed")
    metrics.incr("update_ready_to_experiments.completed")


@app.task
@metrics.timer_decorator("update_launched_experiments.timing")
def update_launched_experiments():
    metrics.incr("update_launched_experiments.started")
    logger.info("Updating launched experiments info")

    launched_experiments = Experiment.objects.filter(
        status__in=[Experiment.STATUS_ACCEPTED, Experiment.STATUS_LIVE]
    )
    for experiment in launched_experiments:
        try:
            logger.info("Updating Experiment: {}".format(experiment))
            if experiment.normandy_id:
                recipe_data = normandy.get_recipe(experiment.normandy_id)

                if needs_to_be_updated(recipe_data, experiment.status):
                    experiment = update_status_task(experiment, recipe_data)

                    if experiment.status == Experiment.STATUS_LIVE:
                        add_start_date_comment_task.delay(experiment.id)
                        email.send_experiment_launch_email(experiment)

                    elif experiment.status == Experiment.STATUS_COMPLETE:
                        comp_experiment_update_res_task.delay(experiment.id)

                if experiment.status == Experiment.STATUS_LIVE:
                    update_population_percent(experiment, recipe_data)
                    set_is_paused_value_task.delay(experiment.id, recipe_data)
                    send_period_ending_emails_task(experiment)
            else:
                logger.info(
                    "Skipping Experiment: {}. No Normandy id found".format(experiment)
                )
        except (IntegrityError, KeyError, normandy.NormandyError) as e:
            logger.info(f"Failed to update Experiment {experiment}: {e}")
            metrics.incr("update_launched_experiments.failed")
    metrics.incr("update_launched_experiments.completed")


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


def update_status_task(experiment, recipe_data):
    logger.info("Updating Experiment Status")
    enabler = normandy.get_recipe_state_enabler(recipe_data)
    old_status = experiment.status
    new_status = STATUS_UPDATE_MAPPING[old_status]
    experiment.status = new_status
    with transaction.atomic():
        experiment.save()

        experiment.changes.create(
            changed_by=enabler, old_status=old_status, new_status=new_status
        )
        metrics.incr("update_experiment_info.updated")
        logger.info("Experiment Status Updated")
    return experiment


@app.task
@metrics.timer_decorator("set_is_paused_value")
def set_is_paused_value_task(experiment_id, recipe_data):
    experiment = Experiment.objects.get(id=experiment_id)
    metrics.incr("set_is_paused_value.started")
    logger.info("Updating Enrollment Value")
    if recipe_data:
        paused_val = is_paused(recipe_data)
        if paused_val is not None and paused_val != experiment.is_paused:
            with transaction.atomic():
                experiment.is_paused = paused_val
                experiment.save()
            metrics.incr("set_is_paused_value.updated")
            logger.info("Enrollment Value Updated")
            message = (
                "Enrollment Completed"
                if experiment.is_paused
                else "Enrollment Re-enabled"
            )
            normandy_user = settings.NORMANDY_DEFAULT_CHANGELOG_USER
            default_user, _ = get_user_model().objects.get_or_create(
                email=normandy_user, username=normandy_user
            )
            experiment.changes.create(message=message, changed_by=default_user)
    metrics.incr("set_is_paused_value.completed")


def update_population_percent(experiment, recipe_data):
    if recipe_data and "filter_object" in recipe_data:
        filter_objects = {f["type"]: f for f in recipe_data["filter_object"]}
        if "bucketSample" in filter_objects:
            bucket_sample = filter_objects["bucketSample"]
            experiment.population_percent = decimal.Decimal(
                bucket_sample["count"] / bucket_sample["total"] * 100
            )
            experiment.save()


def send_period_ending_emails_task(experiment):
    # send experiment ending soon emails if end date is 5 days out
    if experiment.ending_soon:
        if not ExperimentEmail.objects.filter(
            experiment=experiment, type=ExperimentConstants.EXPERIMENT_ENDS
        ).exists():
            email.send_experiment_ending_email(experiment)
            logger.info("Sent ending email for Experiment: {}".format(experiment))
    # send enrollment ending emails if enrollment end
    # date is 5 days out
    if experiment.enrollment_end_date and experiment.enrollment_ending_soon:
        if not ExperimentEmail.objects.filter(
            experiment=experiment, type=ExperimentConstants.EXPERIMENT_PAUSES
        ).exists():
            email.send_enrollment_pause_email(experiment)
            logger.info(
                "Sent enrollment pause email for Experiment: {}".format(experiment)
            )


def needs_to_be_updated(recipe_data, status):
    if recipe_data is None:
        return False

    enabled = recipe_data["enabled"]
    accepted_update = enabled and status == Experiment.STATUS_ACCEPTED
    live_update = not enabled and status == Experiment.STATUS_LIVE
    return accepted_update or live_update


def is_paused(recipe_data):
    arguments = recipe_data.get("arguments", {})
    return arguments.get("isEnrollmentPaused")


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
