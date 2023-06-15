import logging
import sys
from typing import Any, Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from cirrus_sdk import NimbusError  # type: ignore
from fastapi import FastAPI, status
from fml_sdk import FmlError  # type: ignore

from .experiment_recipes import RemoteSettings
from .feature_manifest import FeatureManifestLanguage as FML
from .sdk import SDK
from .settings import channel, context, fml_path, remote_setting_refresh_rate_in_seconds

logger = logging.getLogger(__name__)


def initialize_app():
    app = FastAPI()
    return app


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


def setup():
    app = initialize_app()
    sdk = create_sdk()
    remote_setting = RemoteSettings(sdk)
    fml = create_fml()
    scheduler = create_scheduler()
    return app, sdk, remote_setting, fml, scheduler


app, sdk, remote_setting, fml, scheduler = setup()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/v1/features/", status_code=status.HTTP_200_OK)
async def compute_features():
    # # will recieve as part of incoming request
    targeting_context: Dict[str, Any] = {"clientId": "test", "requestContext": {}}
    enrolled_partial_configuration: Dict[str, Any] = sdk.compute_enrollments(
        targeting_context
    )

    client_feature_configuration: Dict[str, Any] = fml.compute_feature_configurations(
        enrolled_partial_configuration
    )
    return client_feature_configuration


@app.on_event("startup")
async def start_scheduler():
    scheduler.start()
    app.state.scheduler = scheduler


@app.on_event("shutdown")
async def shutdown_scheduler():
    scheduler.shutdown()


async def fetch_schedule_recipes() -> None:
    try:
        remote_setting.fetch_recipes()
    except Exception as e:
        # If an exception is raised, log the error and schedule a retry
        logger.error(f"Failed to fetch recipes: {e}")
        scheduler.add_job(  # type: ignore
            fetch_schedule_recipes,
            "interval",
            seconds=30,
            max_instances=1,
            max_retries=3,
        )


# Schedule the initial job to fetch recipes
scheduler.add_job(  # type: ignore
    fetch_schedule_recipes,
    "interval",
    seconds=remote_setting_refresh_rate_in_seconds,
    max_instances=1,
)
