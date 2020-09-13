import markus
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from mozilla_nimbus_shared import get_data

from experimenter.celery import app
from experimenter.experiments.api.v4.serializers import (
    ExperimentRapidRecipeSerializer,
)
from experimenter.experiments.changelog_utils import (
    update_experiment_with_change_log,
)
from experimenter.experiments.models import (
    Experiment,
    ExperimentBucketNamespace,
    ExperimentBucketRange,
    ExperimentChangeLog,
)
from experimenter.kinto import client

logger = get_task_logger(__name__)
metrics = markus.get_metrics("kinto.tasks")

NIMBUS_DATA = get_data()


@app.task
@metrics.timer_decorator("push_experiment_to_kinto.timing")
def push_experiment_to_kinto(experiment_id):
    metrics.incr("push_experiment_to_kinto.started")

    experiment = Experiment.objects.get(id=experiment_id)
    if not ExperimentBucketRange.objects.filter(experiment=experiment).exists():
        ExperimentBucketNamespace.request_namespace_buckets(
            experiment.recipe_slug,
            experiment,
            NIMBUS_DATA["ExperimentDesignPresets"]["empty_aa"]["preset"]["arguments"][
                "bucketConfig"
            ]["count"],
        )

    data = ExperimentRapidRecipeSerializer(experiment).data

    logger.info(f"Pushing {experiment} to Kinto")

    try:
        client.push_to_kinto(data)

        experimenter_kinto_user, _ = get_user_model().objects.get_or_create(
            email=settings.KINTO_DEFAULT_CHANGELOG_USER,
            username=settings.KINTO_DEFAULT_CHANGELOG_USER,
        )

        changed_values = {
            "recipe": {"new_value": data, "old_value": None, "display_name": "Recipe"}
        }
        ExperimentChangeLog.objects.create(
            experiment=experiment,
            old_status=experiment.status,
            new_status=experiment.status,
            message="Recipe Sent to Kinto",
            changed_values=changed_values,
            changed_by=experimenter_kinto_user,
        )

        logger.info(f"{experiment} pushed to Kinto")
        metrics.incr("push_experiment_to_kinto.completed")
    except Exception as e:
        metrics.incr("push_experiment_to_kinto.failed")
        logger.info(f"Pushing {experiment} to Kinto failed: {e}")
        raise e


def update_rejected_record(record_id, rejected_data):
    experiment = Experiment.objects.get(recipe_slug=record_id)
    update_experiment_with_change_log(
        experiment,
        {"status": Experiment.STATUS_REJECTED},
        settings.KINTO_DEFAULT_CHANGELOG_USER,
        message=rejected_data["last_reviewer_comment"],
    )
    client.delete_rejected_record(record_id)


@app.task
@metrics.timer_decorator("check_kinto_push_queue")
def check_kinto_push_queue():
    metrics.incr("check_kinto_push_queue.started")

    queued_experiments = Experiment.objects.filter(
        type=Experiment.TYPE_RAPID, status=Experiment.STATUS_REVIEW
    ).exclude(bugzilla_id=None)

    if (rejected_collection_data := client.get_rejected_collection_data()) and (
        reject_recipe_id := client.get_rejected_record()
    ):

        update_rejected_record(reject_recipe_id[0], rejected_collection_data)

    if queued_experiments.exists():
        if client.has_pending_review():
            metrics.incr("check_kinto_push_queue.pending_review")
            return

        next_experiment = queued_experiments.first()

        update_experiment_with_change_log(
            next_experiment,
            {
                "status": Experiment.STATUS_ACCEPTED,
                "recipe_slug": next_experiment.generate_recipe_slug(),
            },
            settings.KINTO_DEFAULT_CHANGELOG_USER,
        )

        push_experiment_to_kinto.delay(next_experiment.id)
        metrics.incr("check_kinto_push_queue.queued_experiment_selected")
    else:
        metrics.incr("check_kinto_push_queue.no_experiments_queued")

    metrics.incr("check_kinto_push_queue.completed")


@app.task
@metrics.timer_decorator("check_experiment_is_live")
def check_experiment_is_live():
    metrics.incr("check_experiment_is_live.started")

    accepted_experiments = Experiment.objects.filter(
        type=Experiment.TYPE_RAPID, status=Experiment.STATUS_ACCEPTED
    )

    records = client.get_main_records()
    record_ids = [r.get("id") for r in records]

    for experiment in accepted_experiments:
        if experiment.recipe_slug in record_ids:
            logger.info(
                "{experiment} status is being updated to live".format(
                    experiment=experiment
                )
            )
            update_experiment_with_change_log(
                experiment,
                {"status": Experiment.STATUS_LIVE},
                settings.KINTO_DEFAULT_CHANGELOG_USER,
            )

            logger.info("Experiment Status is set to Live")

    metrics.incr("check_experiment_is_live.completed")


@app.task
@metrics.timer_decorator("check_experiment_is_complete")
def check_experiment_is_complete():
    metrics.incr("check_experiment_is_complete.started")

    live_experiments = Experiment.objects.filter(
        type=Experiment.TYPE_RAPID, status=Experiment.STATUS_LIVE
    )

    records = client.get_main_records()
    record_ids = [r.get("id") for r in records]

    for experiment in live_experiments:
        if experiment.recipe_slug not in record_ids:
            logger.info(
                "{experiment} status is being updated to complete".format(
                    experiment=experiment
                )
            )
            update_experiment_with_change_log(
                experiment,
                {"status": Experiment.STATUS_COMPLETE},
                settings.KINTO_DEFAULT_CHANGELOG_USER,
            )

            logger.info("Experiment Status is set to complete")

    metrics.incr("check_experiment_is_complete.completed")
