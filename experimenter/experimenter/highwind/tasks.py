import markus
import sentry_sdk
from celery.utils.log import get_task_logger
from pydantic import ValidationError

from experimenter.celery import app
from experimenter.experiments.models import NimbusExperiment
from experimenter.highwind.client import blob_path, get_analysis, list_analysis_blobs

logger = get_task_logger(__name__)
metrics = markus.get_metrics("highwind.tasks")


def get_analysis_experiments():
    """Every experiment the job has written a blob for, whatever state it is in.

    Which experiments get analysed is the job's rule, so reading its listing rather than
    filtering on status and dates here keeps that rule in one place, and picks up whatever
    the job starts analysing next without a change on this side. What makes a blob worth
    storing is only whether it is newer than the one we hold.
    """
    blob_paths = list_analysis_blobs()
    slugs = [
        slug
        for slug in NimbusExperiment.objects.values_list("slug", flat=True)
        if blob_path(slug) in blob_paths
    ]

    return NimbusExperiment.objects.filter(slug__in=slugs)


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

    if analysis.metadata.experiment_slug != experiment.slug:
        # The blob name replaces hyphens with underscores, so two slugs differing only
        # there resolve to the same object. The blob names the experiment it analysed, and
        # that is the one it belongs to.
        metrics.incr("fetch_highwind_data.mismatched")
        logger.warning(
            f"Skipping Highwind analysis at {blob_path(experiment.slug)} for"
            f" {experiment.slug}: it analysed {analysis.metadata.experiment_slug}"
        )
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
