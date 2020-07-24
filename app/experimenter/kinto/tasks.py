import datetime

import markus
from celery.utils.log import get_task_logger
from django.conf import settings

from mozilla_nimbus_shared import get_data

from experimenter.celery import app
from experimenter.experiments.api.v4.serializers import ExperimentRapidRecipeSerializer
from experimenter.experiments.changelog_utils import update_experiment_with_change_log
from experimenter.experiments.models import Experiment, ExperimentBucketNamespace
from experimenter.kinto import client


logger = get_task_logger(__name__)
metrics = markus.get_metrics("kinto.tasks")

BUCKET_COUNT = 100
NIMBUS_DATA = get_data()


@app.task
@metrics.timer_decorator("push_experiment_to_kinto.timing")
def push_experiment_to_kinto(experiment_id):
    metrics.incr("push_experiment_to_kinto.started")

    experiment = Experiment.objects.get(id=experiment_id)
    ExperimentBucketNamespace.request_namespace_buckets(
        experiment.normandy_slug,
        experiment,
        NIMBUS_DATA["ExperimentDesignPresets"]["empty_aa"]["preset"]["arguments"][
            "bucketConfig"
        ]["count"],
    )

    data = ExperimentRapidRecipeSerializer(experiment).data

    logger.info(f"Pushing {experiment} to Kinto")

    try:
        client.push_to_kinto(data)

        logger.info(f"{experiment} pushed to Kinto")
        metrics.incr("push_experiment_to_kinto.completed")
    except Exception as e:
        metrics.incr("push_experiment_to_kinto.failed")
        logger.info(f"Pushing {experiment} to Kinto failed: {e}")
        raise e


@app.task
@metrics.timer_decorator("check_kinto_push_queue")
def check_kinto_push_queue():
    metrics.incr("check_kinto_push_queue.started")

    queued_experiments = Experiment.objects.filter(
        type=Experiment.TYPE_RAPID, status=Experiment.STATUS_REVIEW
    )

    if queued_experiments.exists():
        if client.has_pending_review():
            metrics.incr("check_kinto_push_queue.pending_review")
            return

        next_experiment = queued_experiments.first()

        update_experiment_with_change_log(
            next_experiment,
            {
                "status": Experiment.STATUS_ACCEPTED,
                "proposed_start_date": datetime.date.today(),
                "normandy_slug": next_experiment.generate_normandy_slug(),
            },
            settings.KINTO_DEFAULT_CHANGELOG_USER,
        )

        push_experiment_to_kinto.delay(next_experiment.id)
        metrics.incr("check_kinto_push_queue.queued_experiment_selected")
    else:
        metrics.incr("check_kinto_push_queue.no_experiments_queued")

    metrics.incr("check_kinto_push_queue.completed")
