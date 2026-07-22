import markus
import sentry_sdk
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from pydantic import ValidationError

from experimenter.celery import app
from experimenter.experiments.changelog_utils import generate_nimbus_changelog
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusChangeLog, NimbusExperiment
from experimenter.jetstream.client import (
    get_enrollment_funnel_data,
    get_experiment_data,
    get_latest_analysis_start_time,
    get_monitoring_data,
    get_population_sizing_data,
    get_results_filenames,
    get_stored_analysis_start_time,
    has_missing_expected_results,
)
from experimenter.kinto.tasks import get_kinto_user

logger = get_task_logger(__name__)
metrics = markus.get_metrics("jetstream.tasks")


def strip_errors(data):
    """
    Strip errors from result data for meaningful comparison.

    Errors contain timestamps and other metadata that change on every fetch
    even when the actual analysis results are unchanged. We still store errors
    in the database, but don't use them to determine if results have changed.
    """
    if not data:
        return data

    return {
        version_key: {k: v for k, v in version_data.items() if k != "errors"}
        if isinstance(version_data, dict)
        else version_data
        for version_key, version_data in data.items()
    }


@app.task
@metrics.timer_decorator("fetch_experiment_data")
def fetch_experiment_data(experiment_id):
    metrics.incr("fetch_experiment_data.started")
    experiment = None
    try:
        experiment = NimbusExperiment.objects.get(id=experiment_id)
        old_results_data = experiment.results_data
        new_results_data = get_experiment_data(experiment)

        if old_results_data != new_results_data:
            experiment.results_data = new_results_data
            experiment.save()

            old_normalized = strip_errors(old_results_data)
            new_normalized = strip_errors(new_results_data)

            if old_normalized != new_normalized:
                generate_nimbus_changelog(
                    experiment,
                    get_kinto_user(),
                    message=NimbusChangeLog.Messages.RESULTS_UPDATED,
                )

        metrics.incr("fetch_experiment_data.completed")
    except ValidationError as e:
        metrics.incr("fetch_experiment_data.skipped")
        sentry_sdk.capture_exception(e)
        slug = experiment.slug if experiment is not None else experiment_id
        logger.warning(f"Skipping results for {slug}, failed schema validation: {e}")
    except Exception as e:
        metrics.incr("fetch_experiment_data.failed")
        failure_message = f"Fetching experiment data for {experiment_id} "
        if experiment is not None and hasattr(experiment, "slug"):
            failure_message += f"{experiment.slug} "
        failure_message += f"failed: {e}"
        logger.error(failure_message)
        raise e


@app.task
@metrics.timer_decorator("fetch_jetstream_data")
def fetch_jetstream_data():
    metrics.incr("fetch_jetstream_data.started")
    try:
        results_filenames = get_results_filenames()
        for experiment in NimbusExperiment.objects.filter(
            status__in=[NimbusExperiment.Status.COMPLETE, NimbusExperiment.Status.LIVE]
        ):
            latest_analysis_start_time = get_latest_analysis_start_time(experiment.slug)
            needs_missing_results = has_missing_expected_results(
                experiment, results_filenames
            )

            if latest_analysis_start_time is None and not needs_missing_results:
                metrics.incr("fetch_jetstream_data.skipped")
                continue

            stored_analysis_start_time = get_stored_analysis_start_time(experiment)
            has_newer_results = latest_analysis_start_time is not None and (
                stored_analysis_start_time is None
                or stored_analysis_start_time < latest_analysis_start_time
            )

            if has_newer_results or needs_missing_results:
                logger.info(
                    f"Fetching Jetstream data for {experiment.name} ({experiment.slug})"
                )
                fetch_experiment_data.delay(experiment.id)
                metrics.incr("fetch_jetstream_data.completed")
            else:
                logger.info(
                    f"Skipping cache refresh for old experiment {experiment.name}"
                    f" ({experiment.slug})"
                )
                metrics.incr("fetch_jetstream_data.skipped")

    except Exception as e:
        metrics.incr("fetch_jetstream_data.failed")
        logger.error(f"Fetching Jetstream data failed: {e}")
        raise e


@app.task
@metrics.timer_decorator("fetch_population_sizing_data")
def fetch_population_sizing_data():
    metrics.incr("fetch_population_sizing_data.started")
    try:
        sizing_data = get_population_sizing_data()
        sizing = sizing_data.get("v1")

        if sizing is not None:
            cache.set(settings.SIZING_DATA_KEY, sizing.json())

        metrics.incr("fetch_population_sizing_data.completed")
    except Exception as e:
        metrics.incr("fetch_population_sizing_data.failed")
        logger.error(f"Fetching experiment population auto-sizing data failed: {e}")
        raise e


@app.task
@metrics.timer_decorator("fetch_monitoring_data")
def fetch_monitoring_data():
    metrics.incr("fetch_monitoring_data.started")
    try:
        data = get_monitoring_data()

        if not data or "v1" not in data:
            logger.error("No enrollment alert data found in GCS")
            metrics.incr("fetch_monitoring_data.failed")
            return

        alert_data = data.get("v1")

        try:
            funnel_data = get_enrollment_funnel_data()
            funnel_by_slug = funnel_data.get("v1", {}) if funnel_data else {}
        except Exception as e:
            logger.warning(f"Could not fetch enrollment funnel data: {e}")
            funnel_by_slug = {}

        updated_count = 0

        for exp_slug, monitoring_data in alert_data.items():
            try:
                experiment = NimbusExperiment.objects.get(
                    slug=exp_slug,
                    status=NimbusConstants.Status.LIVE,
                )

                merged = {
                    **monitoring_data,
                    "enrollment_funnel": funnel_by_slug.get(exp_slug, []),
                }

                if experiment.monitoring_data != merged:
                    experiment.monitoring_data = merged
                    experiment.monitoring_data_updated_at = timezone.now()
                    experiment.save(
                        update_fields=["monitoring_data", "monitoring_data_updated_at"]
                    )
                    generate_nimbus_changelog(
                        experiment,
                        get_kinto_user(),
                        message=NimbusChangeLog.Messages.MONITORING_DATA_UPDATED,
                    )
                    updated_count += 1

            except NimbusExperiment.DoesNotExist:
                logger.warning(f"Experiment {exp_slug} not found in database")
                continue
            except Exception as e:
                logger.error(f"Failed to update experiment {exp_slug}: {e}")
                continue

        logger.info(
            f"Successfully updated monitoring data for {updated_count} experiments"
        )
        metrics.incr("fetch_monitoring_data.completed")

    except Exception as e:
        metrics.incr("fetch_monitoring_data.failed")
        logger.exception(f"Fatal error in fetch_monitoring_data task: {e}")
        raise


@app.task
@metrics.timer_decorator("update_holdback_enrollment_period")
def update_holdback_enrollment_period():
    metrics.incr("update_holdback_enrollment_period.started")
    try:
        today = timezone.now().date()
        now = timezone.now()

        experiments = NimbusExperiment.objects.filter(
            is_holdback=True,
            status=NimbusExperiment.Status.LIVE,
            _end_date=None,
            _enrollment_end_date=None,
        ).exclude(_start_date=None)

        minimum_days = (
            settings.HOLDBACK_OBSERVATION_DAYS + settings.HOLDBACK_MINIMUM_ENROLLMENT_DAYS
        )
        updated_count = 0
        for experiment in experiments:
            days_since_start = (today - experiment.start_date).days
            if (
                days_since_start < minimum_days
                or days_since_start % settings.HOLDBACK_RERUN_INTERVAL_DAYS != 0
            ):
                logger.debug(
                    f"Skipping holdback {experiment.slug}: "
                    f"days_since_start={days_since_start}, "
                    f"minimum={minimum_days}, "
                    f"interval={settings.HOLDBACK_RERUN_INTERVAL_DAYS}"
                )
                continue

            save_fields = ["do_rerun_timestamp"]
            if not experiment.do_rerun:
                experiment.do_rerun = True
                save_fields.append("do_rerun")
            experiment.do_rerun_timestamp = now
            experiment.save(update_fields=save_fields)
            generate_nimbus_changelog(
                experiment,
                get_kinto_user(),
                message=NimbusChangeLog.Messages.HOLDBACK_ENROLLMENT_UPDATED,
            )
            updated_count += 1

        logger.info(
            f"update_holdback_enrollment_period: updated {updated_count} experiments"
        )
        metrics.incr("update_holdback_enrollment_period.completed")

    except Exception as e:
        metrics.incr("update_holdback_enrollment_period.failed")
        logger.exception(f"Fatal error in update_holdback_enrollment_period: {e}")
        raise
