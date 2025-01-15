import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, List, NamedTuple

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
    context,
    env_name,
    fml_path,
    instance_name,
    metrics_config,
    metrics_path,
    pings_path,
    remote_setting_preview_url,
    remote_setting_refresh_rate_in_seconds,
    remote_setting_url,
)

logger = logging.getLogger(__name__)


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
            traces_sample_rate=0.25,
            # Set profiles_sample_rate to 1.0 to profile 100%
            # of sampled transactions.
            # We recommend adjusting this value in production.
            profiles_sample_rate=0.25,
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
    app.state.scheduler.add_job(
        fetch_schedule_recipes,
        "interval",
        seconds=remote_setting_refresh_rate_in_seconds,
        max_instances=1,
    )


def initialize_glean():
    pings = load_pings(pings_path)
    metrics = load_metrics(metrics_path)

    data_dir_path = Path(metrics_config.data_dir)

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
        data_dir=data_dir_path,
        log_level=int(metrics_config.log_level),
        upload_enabled=metrics_config.upload_enabled,
    )
    return pings, metrics


class EnrollmentMetricData(NamedTuple):
    experiment_slug: str
    branch_slug: str
    experiment_type: str


def collate_enrollment_metric_data(
    enrolled_partial_configuration: dict[str, Any], nimbus_preview_flag: bool
) -> list[EnrollmentMetricData]:
    events: list[dict[str, Any]] = enrolled_partial_configuration.get("events", [])
    data: list[EnrollmentMetricData] = []
    for event in events:
        if event.get("change") == "Enrollment":
            experiment_slug = event.get("experiment_slug", "")
            branch_slug = event.get("branch_slug", "")
            experiment_type = None
            remote_settings = app.state.remote_setting_live
            if nimbus_preview_flag:
                remote_settings = app.state.remote_setting_preview
            experiment_type = remote_settings.get_recipe_type(experiment_slug)
            data.append(
                EnrollmentMetricData(
                    experiment_slug=experiment_slug,
                    branch_slug=branch_slug,
                    experiment_type=experiment_type,
                )
            )
    return data


async def record_metrics(
    enrolled_partial_configuration: dict[str, Any],
    client_id: str,
    nimbus_preview_flag: bool,
):
    metrics = collate_enrollment_metric_data(
        enrolled_partial_configuration=enrolled_partial_configuration,
        nimbus_preview_flag=nimbus_preview_flag,
    )
    for experiment_slug, branch_slug, experiment_type in metrics:
        app.state.metrics.cirrus_events.enrollment.record(
            app.state.metrics.cirrus_events.EnrollmentExtra(
                user_id=client_id,
                app_id=app_id,
                experiment=experiment_slug,
                branch=branch_slug,
                experiment_type=experiment_type,
                is_preview=nimbus_preview_flag,
            )
        )
    app.state.pings.enrollment.submit()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/v1/features/", status_code=status.HTTP_200_OK)
async def compute_features(
    request_data: FeatureRequest,
    nimbus_preview: bool = Query(default=False, alias="nimbus_preview"),
):
    if not request_data.client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client ID value is missing or empty",
        )
    if not request_data.context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Context value is missing or empty",
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
    sdk = app.state.sdk_live
    if nimbus_preview:
        sdk = app.state.sdk_preview
    enrolled_partial_configuration: dict[str, Any] = sdk.compute_enrollments(
        targeting_context
    )

    client_feature_configuration: dict[str, Any] = (
        app.state.fml.compute_feature_configurations(enrolled_partial_configuration)
    )

    await record_metrics(
        enrolled_partial_configuration=enrolled_partial_configuration,
        client_id=request_data.client_id,
        nimbus_preview_flag=nimbus_preview or False,
    )

    return client_feature_configuration


async def fetch_schedule_recipes() -> None:
    live_failed = False
    preview_failed = False

    try:
        app.state.remote_setting_live.fetch_recipes()
    except Exception as e:
        logger.error(f"Failed to fetch live recipes: {e}")
        live_failed = True

    try:
        if app.state.remote_setting_preview:
            app.state.remote_setting_preview.fetch_recipes()
    except Exception as e:
        logger.error(f"Failed to fetch preview recipes: {e}")
        preview_failed = True

    if live_failed or preview_failed:
        schedule_retry()


def schedule_retry():
    app.state.scheduler.add_job(
        fetch_schedule_recipes,
        "interval",
        seconds=30,
        max_instances=1,
        max_retries=3,
    )


@app.get("/__lbheartbeat__")
async def health_check_lbheartbeat():
    return {"status": "ok"}


@app.get("/__heartbeat__")
async def health_check_heartbeat():
    return {"status": "ok"}
