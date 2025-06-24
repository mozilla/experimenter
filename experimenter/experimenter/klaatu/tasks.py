import markus
import requests
from celery.utils.log import get_task_logger
from packaging import version

from experimenter.celery import app
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.klaatu.client import (
    KlaatuClient,
    KlaatuError,
    KlaatuTargets,
    KlaatuWorkflows,
)

logger = get_task_logger(__name__)
metrics = markus.get_metrics("klaatu.nimbus_tasks")


def get_release_version() -> int:
    versions = requests.get("https://whattrainisitnow.com/api/firefox/releases/").json()
    version = list(versions.keys())[-1]
    return version


def get_workflow(application: str) -> str:
    match application:
        case "windows":
            return KlaatuWorkflows.WINDOWS
        case "linux":
            return KlaatuWorkflows.LINUX
        case "macos":
            return KlaatuWorkflows.MACOS
        case "fenix":
            return KlaatuWorkflows.ANDROID
        case "ios":
            return KlaatuWorkflows.IOS
        case _:
            raise KlaatuError("Application selection not allowed.")


def get_firefox_targets(experiment: NimbusExperiment) -> list[str]:
    versions = []
    release_version = get_release_version()
    latest_per_major = {}
    final_versions = []
    max_version = None

    # get max version
    try:
        max_version = int(float(experiment.firefox_max_version.replace("!", "0"))) + 1
    except ValueError:
        max_version = release_version

    # if no max version they want to test against release, so include nightly/beta
    if "desktop" in experiment.application and experiment.firefox_max_version == "":
        final_versions.extend(
            [KlaatuTargets.LATEST_NIGHTLY.value, KlaatuTargets.LATEST_BETA.value]
        )

    # fill versions up to max version
    for _version in NimbusConstants.Version:
        _version = _version.value.replace("!", "0")
        if version.parse(_version) >= version.parse(
            experiment.firefox_min_version.replace("!", "0")
        ) and version.parse(_version) < version.parse(str(max_version)):
            versions.append(_version)

    for v in versions:
        parsed_version = version.parse(v)
        major = parsed_version.release[0]  # type: ignore

        if major not in latest_per_major or parsed_version > latest_per_major[major]:
            latest_per_major[major] = parsed_version

    final_versions.extend([str(v) for v in latest_per_major.values()])

    return final_versions


def get_branches(experiment: NimbusExperiment) -> list[str]:
    branches = [experiment.reference_branch.slug]  # type: ignore
    branches.extend([branch.slug for branch in experiment.treatment_branches])
    return branches


def create_klaatu_client(experiment: NimbusExperiment, application: str) -> KlaatuClient:
    workflow = get_workflow(application)
    client = KlaatuClient(workflow)
    return client


@app.task
def klaatu_start_job(experiment: NimbusExperiment, application: str) -> None:
    client = create_klaatu_client(experiment, application)
    firefox_targets = get_firefox_targets(experiment)
    branches = get_branches(experiment)
    client.run_test(
        experiment_slug=experiment.slug, branch_slugs=branches, targets=firefox_targets
    )


@app.task
def klaatu_get_run_id(experiment: NimbusExperiment, application: str) -> None:
    client = create_klaatu_client(experiment, application)
    run_id = client.find_run_id(
        experiment_slug=experiment.slug, dispatched_at=experiment.published_date
    )
    experiment.klaatu_recent_run_id = run_id
    experiment.save()


@app.task
def klaatu_check_job_complete(experiment: NimbusExperiment, application: str) -> None:
    client = create_klaatu_client(experiment, application)
    client.is_job_complete(job_id=experiment.klaatu_recent_run_id)
    if client.is_job_complete(job_id=experiment.klaatu_recent_run_id):
        experiment.klaatu_status = True
        experiment.save()
