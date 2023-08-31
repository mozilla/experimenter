import datetime as dt

import markus
from celery.utils.log import get_task_logger
from django.core.cache import cache

from experimenter.celery import app
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.jetstream.client import get_experiment_data, get_population_sizing_data
from experimenter.settings import SIZING_DATA_KEY

logger = get_task_logger(__name__)
metrics = markus.get_metrics("jetstream.tasks")


@app.task
@metrics.timer_decorator("fetch_experiment_data")
def fetch_experiment_data(experiment_id):
    metrics.incr("fetch_experiment_data.started")
    experiment = None
    try:
        experiment = NimbusExperiment.objects.get(id=experiment_id)
        experiment.results_data = get_experiment_data(experiment)
        experiment.save()
        metrics.incr("fetch_experiment_data.completed")
    except Exception as e:
        metrics.incr("fetch_experiment_data.failed")
        failure_message = f"Fetching experiment data for {experiment_id} "
        if experiment is not None and hasattr(experiment, "slug"):
            failure_message += f"{experiment.slug} "
        failure_message += f"failed: {e}"
        logger.info(failure_message)
        raise e


@app.task
@metrics.timer_decorator("fetch_jetstream_data")
def fetch_jetstream_data():
    metrics.incr("fetch_jetstream_data.started")
    try:
        for experiment in NimbusExperiment.objects.filter(
            status__in=[NimbusExperiment.Status.COMPLETE, NimbusExperiment.Status.LIVE]
        ):
            if (
                experiment.status == NimbusExperiment.Status.LIVE
                or experiment.results_data is None
                or (
                    experiment.computed_end_date
                    and (
                        experiment.computed_end_date
                        + dt.timedelta(days=NimbusConstants.DAYS_ANALYSIS_BUFFER)
                    )
                    >= dt.date.today()
                )
            ):
                logger.info(
                    f"Fetching Jetstream data for {experiment.name} ({experiment.slug})"
                )
                fetch_experiment_data.delay(experiment.id)
                metrics.incr("fetch_jetstream_data.completed")
            else:
                metrics.incr("fetch_jetstream_data.skipped")
                logger.info(
                    f"Skipping cache refresh for old experiment {experiment.name}"
                    f" ({experiment.slug})"
                )

    except Exception as e:
        metrics.incr("fetch_jetstream_data.failed")
        logger.info(f"Fetching Jetstream data failed: {e}")
        raise e


@app.task
@metrics.timer_decorator("fetch_population_sizing_data")
def fetch_population_sizing_data():
    metrics.incr("fetch_population_sizing_data.started")
    try:
        sizing_data = get_population_sizing_data()
        sizing = sizing_data.get("v1")

        cache.set(SIZING_DATA_KEY, sizing)
        metrics.incr("fetch_population_sizing_data.completed")
    except Exception as e:
        metrics.incr("fetch_population_sizing_data.failed")
        logger.error(f"Fetching experiment population auto-sizing data failed: {e}")
        raise e
