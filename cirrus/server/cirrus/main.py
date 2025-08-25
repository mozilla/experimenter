import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, List, NamedTuple, TypedDict

import sentry_sdk
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from cirrus_sdk import NimbusError  # type: ignore
from fastapi import FastAPI, HTTPException, Query, status
from fml_sdk import FmlError  # type: ignore
from glean import Configuration, Glean, load_metrics, load_pings  # type: ignore
from pydantic import BaseModel

from .experiment_recipes import RemoteSettings
from .feature_manifest import FeatureManifestLanguage as FML
from .sdk import SDK, CirrusMetricsHandler
from .settings import (
    app_id,
    channel,
    cirrus_sentry_dsn,
    cirrus_sentry_profiles_sample_rate,
    cirrus_sentry_traces_sample_rate,
    context,
    env_name,
    fml_path,
    instance_name,
    metrics_config,
    metrics_path,
    pings_path,
    remote_setting_preview_url,
    remote_setting_refresh_max_attempts,
    remote_setting_refresh_rate_in_seconds,
    remote_setting_refresh_retry_delay_in_seconds,
    remote_setting_url,
)

logger = logging.getLogger(__name__)

FETCH_SCHEDULE_RECIPES_JOB_ID = "FETCH_SCHEDULE_RECIPES_JOB_ID"


class FeatureRequest(BaseModel):
    client_id: str
    context: dict[str, Any]


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_sentry()
    verify_settings()
    app.state.pings, app.state.metrics = initialize_glean()
    app.state.fml = create_fml()
    app.state.sdk_live = create_sdk(
        app.state.fml.get_coenrolling_feature_ids(),
        CirrusMetricsHandler(app.state.metrics, app.state.pings),
    )
    app.state.sdk_preview = create_sdk(
        app.state.fml.get_coenrolling_feature_ids(),
        CirrusMetricsHandler(app.state.metrics, app.state.pings),
    )

    app.state.remote_setting_live = RemoteSettings(remote_setting_url, app.state.sdk_live)
    app.state.remote_setting_preview = RemoteSettings(
        remote_setting_preview_url, app.state.sdk_preview
    )

    app.state.scheduler = create_scheduler()
    start_and_set_initial_job()
    send_instance_name_metric()

    yield
    if app.state.scheduler:
        app.state.scheduler.shutdown()
    Glean.shutdown()


def send_instance_name_metric():
    app.state.metrics.cirrus_events.instance_name.set(instance_name)
    app.state.pings.startup.submit()


def initialize_sentry():
    if cirrus_sentry_dsn:  # pragma: no cover
        sentry_sdk.init(
            dsn=cirrus_sentry_dsn,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=cirrus_sentry_traces_sample_rate,
            # Set profiles_sample_rate to 1.0 to profile 100%
            # of sampled transactions.
            # We recommend adjusting this value in production.
            profiles_sample_rate=cirrus_sentry_profiles_sample_rate,
            environment=env_name,
        )


def verify_settings():
    if not remote_setting_url:
        logger.error("Remote setting URL is required but not provided.")
        sys.exit(1)


def create_fml():
    try:
        return FML(fml_path=fml_path, channel=channel)
    except FmlError as e:  # type: ignore
        logger.error(f"Error occurred during FML creation: {e}")
        sys.exit(1)


def create_sdk(coenrolling_feature_ids: List[str], metrics_handler: CirrusMetricsHandler):
    try:
        return SDK(
            context=context,
            metrics_handler=metrics_handler,
            coenrolling_feature_ids=coenrolling_feature_ids,
        )
    except NimbusError as e:  # type: ignore
        logger.error(f"Error occurred during SDK creation: {e}")
        sys.exit(1)


def create_scheduler():
    return AsyncIOScheduler(
        job_defaults={
            "coalesce": False,
            "max_instances": 3,
            "misfire_grace_time": 60,
        }
    )


def start_and_set_initial_job():
    app.state.scheduler.start()
    schedule_next_attempt(attempt=1, failed=False)


def initialize_glean():
    pings = load_pings(pings_path)
    metrics = load_metrics(metrics_path)

    config = Configuration(
        channel=metrics_config.channel,
        max_events=metrics_config.max_events_buffer,
        server_endpoint=metrics_config.server_endpoint,
    )

    Glean.initialize(
        application_build_id=metrics_config.build,
        application_id=metrics_config.app_id,
        application_version=metrics_config.version,
        configuration=config,
        data_dir=metrics_config.data_dir,
        log_level=int(metrics_config.log_level),
        upload_enabled=metrics_config.upload_enabled,
    )
    return pings, metrics


class EnrollmentMetricData(NamedTuple):
    nimbus_user_id: str
    app_id: str
    experiment_slug: str
    branch_slug: str
    experiment_type: str
    is_preview: bool


class ComputeFeaturesEnrollmentResult(TypedDict):
    features: dict[str, dict[str, Any]]
    enrollments: list[EnrollmentMetricData]


def collate_enrollment_metric_data(
    enrolled_partial_configuration: dict[str, Any],
    client_id: str,
    nimbus_preview_flag: bool,
) -> list[EnrollmentMetricData]:
    events: list[dict[str, Any]] = enrolled_partial_configuration.get("events", [])
    remote_settings = (
        app.state.remote_setting_preview
        if nimbus_preview_flag
        else app.state.remote_setting_live
    )
    data: list[EnrollmentMetricData] = []
    for event in events:
        if event.get("change") == "Enrollment":
            experiment_slug = event.get("experiment_slug", "")
            branch_slug = event.get("branch_slug", "")
            experiment_type = remote_settings.get_recipe_type(experiment_slug)
            data.append(
                EnrollmentMetricData(
                    nimbus_user_id=client_id,
                    app_id=app_id,
                    experiment_slug=experiment_slug,
                    branch_slug=branch_slug,
                    experiment_type=experiment_type,
                    is_preview=nimbus_preview_flag,
                )
            )
    return data


async def record_metrics(enrollment_data: list[EnrollmentMetricData]):
    for enrollment in enrollment_data:
        app.state.metrics.cirrus_events.enrollment.record(
            app.state.metrics.cirrus_events.EnrollmentExtra(
                nimbus_user_id=enrollment.nimbus_user_id,
                app_id=enrollment.app_id,
                experiment=enrollment.experiment_slug,
                branch=enrollment.branch_slug,
                experiment_type=enrollment.experiment_type,
                is_preview=enrollment.is_preview,
            )
        )
    app.state.pings.enrollment.submit()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


async def compute_features_enrollments(
    request_data: FeatureRequest,
    nimbus_preview: bool = Query(default=False, alias="nimbus_preview"),
) -> ComputeFeaturesEnrollmentResult:
    if not request_data.client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client ID value is missing or empty",
        )
    if nimbus_preview and not remote_setting_preview_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This Cirrus doesn’t support preview mode",
        )

    targeting_context = {
        "clientId": request_data.client_id,
        "requestContext": request_data.context,
    }

    sdk = app.state.sdk_preview if nimbus_preview else app.state.sdk_live
    enrolled_partial_configuration: dict[str, Any] = sdk.compute_enrollments(
        targeting_context
    )

    client_feature_configuration: dict[str, Any] = (
        app.state.fml.compute_feature_configurations(enrolled_partial_configuration)
    )

    # Enrollments data
    enrollment_data = collate_enrollment_metric_data(
        enrolled_partial_configuration,
        client_id=request_data.client_id,
        nimbus_preview_flag=nimbus_preview,
    )

    # Record metrics
    await record_metrics(enrollment_data)

    return {
        "features": client_feature_configuration,
        "enrollments": enrollment_data,
    }


@app.post("/v1/features/", status_code=status.HTTP_200_OK)
async def compute_features_v1(
    request_data: FeatureRequest,
    nimbus_preview: bool = Query(default=False, alias="nimbus_preview"),
):
    result = await compute_features_enrollments(request_data, nimbus_preview)
    return result["features"]


@app.post("/v2/features/", status_code=status.HTTP_200_OK)
async def compute_features_enrollments_v2(
    request_data: FeatureRequest,
    nimbus_preview: bool = Query(default=False, alias="nimbus_preview"),
):
    result = await compute_features_enrollments(request_data, nimbus_preview)
    return {
        "Features": result["features"],
        "Enrollments": [
            {
                "nimbus_user_id": enrollment.nimbus_user_id,
                "app_id": enrollment.app_id,
                "experiment": enrollment.experiment_slug,
                "branch": enrollment.branch_slug,
                "experiment_type": enrollment.experiment_type,
                "is_preview": enrollment.is_preview,
            }
            for enrollment in result["enrollments"]
        ],
    }


async def fetch_schedule_recipes(attempt: int = 0) -> None:
    failed = False

    try:
        app.state.remote_setting_live.fetch_recipes()
    except Exception as e:
        logger.error(f"Failed to fetch live recipes: {e}")
        failed = True

    try:
        if app.state.remote_setting_preview:
            app.state.remote_setting_preview.fetch_recipes()
    except Exception as e:
        logger.error(f"Failed to fetch preview recipes: {e}")
        failed = True

    schedule_next_attempt(attempt=attempt, failed=failed)


def schedule_next_attempt(attempt: int, failed: bool):
    if attempt == 0 and not failed:
        pass
    elif attempt < remote_setting_refresh_max_attempts and failed:
        # increase attempt and set retry delay
        app.state.scheduler.add_job(
            fetch_schedule_recipes,
            "interval",
            seconds=remote_setting_refresh_retry_delay_in_seconds,
            max_instances=1,
            id=FETCH_SCHEDULE_RECIPES_JOB_ID,
            replace_existing=True,
            kwargs={"attempt": attempt + 1},
        )
    else:
        # reset attempt and set refresh rate
        app.state.scheduler.add_job(
            fetch_schedule_recipes,
            "interval",
            seconds=remote_setting_refresh_rate_in_seconds,
            max_instances=1,
            id=FETCH_SCHEDULE_RECIPES_JOB_ID,
            replace_existing=True,
        )


@app.get("/__lbheartbeat__")
async def health_check_lbheartbeat():
    return {"status": "ok"}


@app.get("/__heartbeat__")
async def health_check_heartbeat():
    return {"status": "ok"}
