import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from decouple import config  # type: ignore
from fastapi import FastAPI, status

from .experiment_recipes import RemoteSettings
from .feature_manifest import FeatureManifestLanguage as FML
from .manifest_loader import ManifestLoader
from .sdk import SDK

logger = logging.getLogger(__name__)

app = FastAPI()
remote_setting = RemoteSettings()
sdk = SDK()
manifest_loader = ManifestLoader()
fml = FML()


remote_setting_refresh_rate_in_seconds: int = int(
    config("REMOTE_SETTING_REFRESH_RATE_IN_SECONDS")  # type: ignore
)


# Set up scheduler with ThreadPoolExecutor and configure job options
scheduler: AsyncIOScheduler = AsyncIOScheduler(
    job_defaults={"coalesce": False, "max_instances": 3, "misfire_grace_time": 60},
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/enrollment_status", status_code=status.HTTP_200_OK)
async def compute_enrollment_status():
    recipes = remote_setting.get_recipes()
    # will recieve as part of incoming request
    targeting_context = {"client_id": "testid"}
    enrolled_partial_configuration = sdk.compute_enrollments(recipes, targeting_context)
    feature_configurations = manifest_loader.get_latest_feature_manifest()
    client_feature_configuration = fml.compute_feature_configurations(
        enrolled_partial_configuration, feature_configurations
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
            seconds=remote_setting_refresh_rate_in_seconds,
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
