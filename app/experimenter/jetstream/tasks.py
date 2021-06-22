import datetime

import markus
from celery.utils.log import get_task_logger

from experimenter.celery import app
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.jetstream.client import get_experiment_data

logger = get_task_logger(__name__)
metrics = markus.get_metrics("jetstream.tasks")


@app.task
@metrics.timer_decorator("fetch_experiment_data")
def fetch_experiment_data(experiment_id):
    metrics.incr("fetch_experiment_data.started")
    try:
        experiment = NimbusExperiment.objects.get(id=experiment_id)
        experiment.results_data = get_experiment_data(experiment)
        experiment.save()
        metrics.incr("fetch_experiment_data.completed")
    except Exception as e:
        metrics.incr("fetch_experiment_data.failed")
        logger.info(f"Fetching experiment data for {experiment_id} failed: {e}")
        raise e


@app.task
@metrics.timer_decorator("fetch_jetstream_data")
def fetch_jetstream_data():
    metrics.incr("fetch_jetstream_data.started")
    try:
        for experiment in NimbusExperiment.objects.all().exclude(
            status__in=[NimbusExperiment.Status.DRAFT]
        ):
            if (
                experiment.results_data is not None
                and experiment.computed_end_date
                and (
                    experiment.computed_end_date
                    + datetime.timedelta(days=NimbusConstants.DAYS_ANALYSIS_BUFFER)
                )
                < datetime.date.today()
            ):
                metrics.incr("fetch_jetstream_data.skipped")
                logger.info(
                    "Skipping cache refresh for old experiment {name}".format(
                        name=experiment.name
                    )
                )

                continue

            logger.info("Fetching Jetstream data for {name}".format(name=experiment.name))
            fetch_experiment_data.delay(experiment.id)
            metrics.incr("fetch_jetstream_data.completed")
    except Exception as e:
        metrics.incr("fetch_jetstream_data.failed")
        logger.info(f"Fetching Jetstream data failed: {e}")
        raise e
