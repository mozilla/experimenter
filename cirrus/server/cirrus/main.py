import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from cirrus_sdk import NimbusError  # type: ignore
from fastapi import FastAPI, HTTPException, status
from fml_sdk import FmlError  # type: ignore
from pydantic import BaseModel

from glean import Configuration, Glean, load_metrics, load_pings  # type: ignore

from .experiment_recipes import RemoteSettings
from .feature_manifest import FeatureManifestLanguage as FML
from .sdk import SDK
from .settings import (
    app_id,
    channel,
    context,
    fml_path,
    metrics_config,
    metrics_path,
    pings_path,
    remote_setting_refresh_rate_in_seconds,
)

logger = logging.getLogger(__name__)


class FeatureRequest(BaseModel):
    client_id: str
    context: Dict[str, Any]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sdk = create_sdk()
    app.state.remote_setting = RemoteSettings(app.state.sdk)
    app.state.fml = create_fml()
    app.state.scheduler = create_scheduler()
    start_and_set_initial_job()
    app.state.pings, app.state.metrics = initialize_glean()

    yield
    if app.state.scheduler:
        app.state.scheduler.shutdown()


def create_fml():
    try:
        fml = FML(fml_path=fml_path, channel=channel)
        return fml
    except FmlError as e:
        logger.error(f"Error occurred during FML creation: {e}")
        sys.exit(1)


def create_sdk():
    try:
        sdk = SDK(context=context)
        return sdk
    except NimbusError as e:
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


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/v1/features/", status_code=status.HTTP_200_OK)
async def compute_features(request_data: FeatureRequest):
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
    targeting_context: Dict[str, Any] = {
        "clientId": request_data.client_id,
        "requestContext": request_data.context,
    }
    enrolled_partial_configuration: Dict[str, Any] = app.state.sdk.compute_enrollments(
        targeting_context
    )
    client_feature_configuration: Dict[
        str, Any
    ] = app.state.fml.compute_feature_configurations(enrolled_partial_configuration)

    return client_feature_configuration


async def fetch_schedule_recipes() -> None:
    try:
        app.state.remote_setting.fetch_recipes()
    except Exception as e:
        # If an exception is raised, log the error and schedule a retry
        logger.error(f"Failed to fetch recipes: {e}")
        app.state.scheduler.add_job(
            fetch_schedule_recipes,
            "interval",
            seconds=30,
            max_instances=1,
            max_retries=3,
        )
