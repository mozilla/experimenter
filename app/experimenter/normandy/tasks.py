import decimal

import markus
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from experimenter.bugzilla.tasks import (
    add_start_date_comment_task,
    comp_experiment_update_res_task,
)
from experimenter.celery import app
from experimenter.legacy.legacy_experiments.changelog_utils import (
    update_experiment_with_change_log,
)
from experimenter.legacy.legacy_experiments.email import (
    send_experiment_launch_email,
    send_period_ending_emails_task,
)
from experimenter.legacy.legacy_experiments.models import Experiment
from experimenter.normandy import client as normandy

STATUS_UPDATE_MAPPING = {
    Experiment.STATUS_ACCEPTED: Experiment.STATUS_LIVE,
    Experiment.STATUS_LIVE: Experiment.STATUS_COMPLETE,
}

logger = get_task_logger(__name__)
metrics = markus.get_metrics("experiments.tasks")

QA_LAUNCH_MESSAGE = "Launched for QA"


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
                sorted_recipe_data = sorted(recipe_data, key=lambda x: x.get("id"))
                recipe_ids = [r["id"] for r in sorted_recipe_data]
                changed_data = {
                    "normandy_id": recipe_ids[0],
                    "other_normandy_ids": recipe_ids[1:],
                    "status": Experiment.STATUS_ACCEPTED,
                }
                user_email = (
                    sorted_recipe_data[0]
                    .get("latest_revision", {})
                    .get("creator", {})
                    .get("email", "")
                ) or settings.NORMANDY_DEFAULT_CHANGELOG_USER

                update_experiment_with_change_log(experiment, changed_data, user_email)

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
                        send_experiment_launch_email(experiment)

                    elif experiment.status == Experiment.STATUS_COMPLETE:
                        comp_experiment_update_res_task.delay(experiment.id)

                if experiment.status == Experiment.STATUS_LIVE:
                    update_is_high_population(experiment, recipe_data)
                    update_population_info(experiment, recipe_data)
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


def is_qaOnly(recipe_data):
    if "filter_object" in recipe_data:
        filter_objects = {f["type"]: f for f in recipe_data["filter_object"]}
        return "qaOnly" in filter_objects


def is_alreadyQALaunched(experiment):
    return experiment.changes.filter(
        message=QA_LAUNCH_MESSAGE,
    ).exists()


def update_status_task(experiment, recipe_data):
    logger.info("Updating Experiment Status")
    enabler = normandy.get_recipe_state_enabler(recipe_data)

    if is_qaOnly(recipe_data):
        if not is_alreadyQALaunched(experiment):
            experiment.changes.create(
                changed_by=enabler,
                old_status=experiment.status,
                new_status=experiment.status,
                message=QA_LAUNCH_MESSAGE,
            )

    else:
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


def update_population_info(experiment, recipe_data):
    if recipe_data and "filter_object" in recipe_data:
        filter_objects = {f["type"]: f for f in recipe_data["filter_object"]}
        update_population_percent(experiment, recipe_data, filter_objects)
        update_firefox_versions(experiment, recipe_data, filter_objects)


def update_population_percent(experiment, recipe_data, filter_objects):

    changed_data = {}
    if bucket_sample := filter_objects.get("bucketSample") or filter_objects.get(
        "namespaceSample"
    ):

        decimal.getcontext().prec = 5
        bucket_total = bucket_sample.get("total", experiment.BUCKET_TOTAL)
        percent_decimal = (
            decimal.Decimal(bucket_sample["count"])
            / decimal.Decimal(bucket_total)
            * decimal.Decimal(100)
        )

        if experiment.population_percent != percent_decimal:
            changed_data = {"population_percent": percent_decimal}

    if changed_data:
        user_email = (
            recipe_data.get("creator", {}).get("email", "")
        ) or settings.NORMANDY_DEFAULT_CHANGELOG_USER
        update_experiment_with_change_log(
            experiment, changed_data, user_email, message="Updated Population Percent"
        )


def update_firefox_versions(experiment, recipe_data, filter_objects):
    changed_data = {}

    if versions := filter_objects.get("version"):

        min_version = str(float(min(versions["versions"])))
        max_version = str(float(max(versions["versions"])))
        if experiment.firefox_min_version != min_version:
            changed_data["firefox_min_version"] = min_version
        if experiment.firefox_max_version != max_version:
            changed_data["firefox_max_version"] = max_version

        if changed_data:
            user_email = (
                recipe_data.get("creator", {}).get("email", "")
            ) or settings.NORMANDY_DEFAULT_CHANGELOG_USER
            update_experiment_with_change_log(
                experiment, changed_data, user_email, message="Added Version(s)"
            )


def update_is_high_population(experiment, recipe_data):
    recipe_args = recipe_data.get("arguments", {})
    if recipe_is_high_population := recipe_args.get("isHighPopulation"):
        if experiment.is_high_population != recipe_is_high_population:
            logger.info(
                "{experiment}: Setting is_high_population to {high_pop_val}".format(
                    experiment=experiment, high_pop_val=recipe_is_high_population
                )
            )
            experiment.is_high_population = recipe_is_high_population
            experiment.save()


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
