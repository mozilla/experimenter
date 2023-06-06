import logging
from typing import Any, Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from fastapi import FastAPI, status

from .experiment_recipes import remote_setting
from .feature_manifest import fml
from .sdk import sdk
from .settings import remote_setting_refresh_rate_in_seconds

logger = logging.getLogger(__name__)

app = FastAPI()


# Set up scheduler with ThreadPoolExecutor and configure job options
scheduler: AsyncIOScheduler = AsyncIOScheduler(
    job_defaults={"coalesce": False, "max_instances": 3, "misfire_grace_time": 60},
)


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
