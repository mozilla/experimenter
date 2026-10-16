import datetime

import markus
import sentry_sdk
from celery.utils.log import get_task_logger
from django.db.models import Q
from django.utils import timezone
from pydantic import ValidationError

from experimenter.celery import app
from experimenter.experiments.models import NimbusExperiment
from experimenter.highwind.client import get_analysis

logger = get_task_logger(__name__)
metrics = markus.get_metrics("highwind.tasks")

# The job selects an experiment for as long as the run date has not passed its end
# date, so the last blob an experiment ever gets is written on the end date itself and
# does not change after. A week of slack covers the run that writes it, and any retry,
# without reading back blobs that have been final for months.
COMPLETED_LOOKBACK_DAYS = 7


def get_analysis_experiments(as_of=None):
    """The experiments the Highwind job could have written a blob for this run."""
    as_of = as_of or timezone.now().date()
    completed_since = as_of - datetime.timedelta(days=COMPLETED_LOOKBACK_DAYS)

    return NimbusExperiment.objects.filter(
        Q(status=NimbusExperiment.Status.LIVE)
        | Q(
            status=NimbusExperiment.Status.COMPLETE,
            _computed_end_date__gte=completed_since,
        )
    )


def load_experiment_analysis(experiment):
    """Store the experiment's published analysis if it is newer than what we hold."""
    try:
        analysis = get_analysis(experiment)
    except ValidationError as e:
        # The stored analysis is left alone: a blob we cannot read says nothing about
        # whether what we already have is still good.
        metrics.incr("fetch_highwind_data.invalid")
        logger.warning(
            f"Skipping Highwind analysis for {experiment.slug},"
            f" failed schema validation: {e}"
        )
        sentry_sdk.capture_exception(e)
        return
    except Exception as e:
        # One experiment's blob failing to read should not cost every experiment after it
        # its hourly refresh, so this is reported rather than raised.
        metrics.incr("fetch_highwind_data.failed")
        logger.error(f"Fetching Highwind analysis for {experiment.slug} failed: {e}")
        sentry_sdk.capture_exception(e)
        return

    if analysis is None:
        metrics.incr("fetch_highwind_data.missing")
        return

    generated_at = analysis.metadata.generated_at
    if (
        experiment.analysis_last_updated is not None
        and generated_at <= experiment.analysis_last_updated
    ):
        metrics.incr("fetch_highwind_data.unchanged")
        return

    logger.info(f"Loading Highwind analysis for {experiment.slug}")
    experiment.analysis_data = analysis.model_dump(mode="json")
    experiment.analysis_last_updated = generated_at
    # No changelog, and only these two columns: loading results is not a change anyone
    # made to the experiment, so it should neither appear in the history nor move the
    # experiment to the top of a list sorted by last updated.
    experiment.save(update_fields=["analysis_data", "analysis_last_updated"])
    metrics.incr("fetch_highwind_data.loaded")


@app.task
@metrics.timer_decorator("fetch_highwind_data")
def fetch_highwind_data():
    metrics.incr("fetch_highwind_data.started")

    for experiment in get_analysis_experiments():
        load_experiment_analysis(experiment)

    metrics.incr("fetch_highwind_data.completed")
