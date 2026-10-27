import markus
import sentry_sdk
from celery.utils.log import get_task_logger
from pydantic import ValidationError

from experimenter.celery import app
from experimenter.experiments.models import NimbusExperiment
from experimenter.highwind.client import (
    UnsupportedSchemaError,
    blob_path,
    get_analysis,
    list_analysis_blobs,
)

logger = get_task_logger(__name__)
metrics = markus.get_metrics("highwind.tasks")


def get_analysis_experiments():
    # Which experiments get analysed is the job's rule, so this reads its listing rather
    # than filtering on status and dates. The only gate is whether a blob is newer than
    # the one we hold.
    blob_paths = list_analysis_blobs()
    slugs = [
        slug
        for slug in NimbusExperiment.objects.values_list("slug", flat=True)
        if blob_path(slug) in blob_paths
    ]

    return NimbusExperiment.objects.filter(slug__in=slugs)


def load_experiment_analysis(experiment):
    try:
        analysis = get_analysis(experiment)
    except UnsupportedSchemaError as e:
        # Not reported: the job does not rewrite a blob for an experiment that has
        # ended, so there is nothing a later run can resolve.
        metrics.incr("fetch_highwind_data.unsupported")
        logger.warning(f"Skipping Highwind analysis for {experiment.slug}: {e}")
        return
    except ValidationError as e:
        # Stored data is left alone: an unreadable blob says nothing about whether what
        # we already hold is still good.
        metrics.incr("fetch_highwind_data.invalid")
        logger.warning(
            f"Skipping Highwind analysis for {experiment.slug},"
            f" failed schema validation: {e}"
        )
        sentry_sdk.capture_exception(e)
        return
    except Exception as e:
        # Reported rather than raised, so one bad blob does not cost every experiment
        # after it its refresh.
        metrics.incr("fetch_highwind_data.failed")
        logger.error(f"Fetching Highwind analysis for {experiment.slug} failed: {e}")
        sentry_sdk.capture_exception(e)
        return

    if analysis is None:
        metrics.incr("fetch_highwind_data.missing")
        return

    if analysis.metadata.experiment_slug != experiment.slug:
        # The blob name maps hyphens to underscores, so two slugs differing only there
        # resolve to the same object. The blob names which one it analysed.
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
    # made, so it should not appear in the history or reorder a list sorted by updated.
    experiment.save(update_fields=["analysis_data", "analysis_last_updated"])
    metrics.incr("fetch_highwind_data.loaded")


@app.task
@metrics.timer_decorator("fetch_highwind_data")
def fetch_highwind_data():
    metrics.incr("fetch_highwind_data.started")

    for experiment in get_analysis_experiments():
        load_experiment_analysis(experiment)

    metrics.incr("fetch_highwind_data.completed")
