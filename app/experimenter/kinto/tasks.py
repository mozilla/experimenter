import markus
from celery.utils.log import get_task_logger

from experimenter.celery import app
from experimenter.experiments.models import Experiment
from experimenter.kinto import client


logger = get_task_logger(__name__)
metrics = markus.get_metrics("kinto.tasks")


@app.task
@metrics.timer_decorator("push_experiment_to_kinto.timing")
def push_experiment_to_kinto(experiment_id):
    metrics.incr("push_experiment_to_kinto.started")

    experiment = Experiment.objects.get(id=experiment_id)
    logger.info(f"Pushing {experiment} to Kinto")

    try:
        client.push_to_kinto({"slug": experiment.slug})

        logger.info(f"{experiment} pushed to Kinto")
        metrics.incr("push_experiment_to_kinto.completed")
    except Exception as e:
        metrics.incr("push_experiment_to_kinto.failed")
        logger.info(f"Pushing {experiment} to Kinto failed: {e}")
        raise e
