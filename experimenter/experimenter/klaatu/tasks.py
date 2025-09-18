import time

import jwt
import markus
import requests
from celery.utils.log import get_task_logger
from django.conf import settings
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
parse = NimbusConstants.Version.parse


def _create_auth_token() -> str:
    app_id = settings.GH_APP_ID
    installation_id = settings.GH_INSTALLATION_ID
    private_key = settings.GH_APP_PRIVATE_KEY.replace("\\n", "\n")

    now = int(time.time())
    payload = {"iat": now, "exp": now + 540, "iss": app_id}
    jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

    # Get installation token
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers=headers,
    )
    token = response.json()["token"]
    return token


def get_release_version() -> int:
    versions = requests.get(NimbusConstants.WHAT_TRAIN_IS_IT_NOW_URL).json()
    version = list(versions.keys())[-1]
    return version


def get_workflows(application: str) -> list[str]:
    match application:
        case NimbusConstants.Application.DESKTOP:
            return [
                KlaatuWorkflows.WINDOWS.value,
                KlaatuWorkflows.LINUX.value,
                KlaatuWorkflows.MACOS.value,
            ]
        case NimbusConstants.Application.FENIX:
            return [KlaatuWorkflows.ANDROID.value]
        case NimbusConstants.Application.IOS:
            return [KlaatuWorkflows.IOS.value]
        case _:
            raise KlaatuError("Application selection not allowed.")


def get_firefox_targets(experiment: NimbusExperiment) -> list[str]:
    versions = []
    release_version = get_release_version()
    latest_per_major = {}
    final_versions = []
    max_version = None
    exp_max_version = parse(f"{experiment.firefox_max_version}")

    # get max version
    try:
        max_version = int(float(f"{exp_max_version}")) + 1
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
        if version.parse(_version) >= parse(
            experiment.firefox_min_version
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


def create_klaatu_clients(application: str, token: str) -> list[KlaatuClient]:
    clients = []
    workflows = get_workflows(application)
    for workflow in workflows:
        clients.append(KlaatuClient(workflow, _create_auth_token()))
    return clients


@app.task
def klaatu_start_job(experiment: NimbusExperiment, application: str) -> None:
    clients = create_klaatu_clients(application, _create_auth_token())
    firefox_targets = get_firefox_targets(experiment)
    branches = get_branches(experiment)
    server = "prod"
    if settings.IS_STAGING:
        server = "stage"
    for client in clients:
        client.run_test(
            experiment_slug=experiment.slug,
            branch_slugs=branches,
            targets=firefox_targets,
            server=server,
        )


@app.task
def klaatu_get_run_ids(experiment: NimbusExperiment, application: str) -> None:
    client = create_klaatu_clients(application, _create_auth_token())[0]
    run_ids = client.find_run_ids(
        experiment_slug=experiment.slug, dispatched_at=experiment.published_date
    )
    experiment.klaatu_recent_run_ids.extend(run_ids)
    experiment.save()


@app.task
def klaatu_check_jobs_complete(experiment: NimbusExperiment, application: str) -> None:
    client = create_klaatu_clients(application, _create_auth_token())[0]
    job_statuses = []
    for job in experiment.klaatu_recent_run_ids:
        job_statuses.append(client.is_job_complete(job_id=job))
    if True in job_statuses:
        experiment.klaatu_status = True
    else:
        experiment.klaatu_status = False

    experiment.save()
