import datetime
import io
import json
import zipfile
from enum import Enum
from typing import Optional, Union
from urllib.parse import urlencode, urljoin

import requests


class KlaatuStatus(str, Enum):
    COMPLETE = "completed"


class KlaatuWorkflows(str, Enum):
    ANDROID = "android_manual.yml"
    IOS = "ios_manual.yml"
    LINUX = "linux_manual.yml"
    WINDOWS = "windows_manual.yml"
    MACOS = "macos_manual.yml"


class KlaatuEndpoints(str, Enum):
    DISPATCH = "actions/workflows/{workflow}/dispatches"
    RUNS = "actions/workflows/{workflow}/runs"
    RUN_STATUS = "actions/runs/{run_id}"
    ARTIFACTS = "actions/runs/{run_id}/artifacts"


class KlaatuTargets(str, Enum):
    LATEST_DEVEDITION = "latest-devedition"
    LATEST_NIGHTLY = "latest-nightly"
    LATEST_BETA = "latest-beta"
    LATEST_ESR = "latest-esr"
    LATEST_RELEASE = "latest"


class KlaatuError(Exception):
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        self.response_text = response_text
        self.message = message
        super().__init__(self.__str__())

    def __str__(self) -> str:
        message = f"{self.message}"
        if self.status_code:
            message += f": {self.status_code}"
        if self.response_text:
            message += f", {self.response_text}"
        return message


class KlaatuClient:
    def __init__(self, workflow_name: str, token: str) -> None:
        self.workflow_name = workflow_name
        self.auth_token = token
        self.base_url = "https://api.github.com/repos/mozilla/klaatu/"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    def run_test(
        self,
        experiment_slug: str,
        branch_slugs: list[str],
        targets: list[Union[KlaatuTargets, str]],
        server: str = "prod",
    ) -> None:
        path = KlaatuEndpoints.DISPATCH.format(workflow=self.workflow_name)
        url = urljoin(self.base_url, path)

        data = {
            "ref": "main",
            "inputs": {
                "slug": experiment_slug,
                "branch": json.dumps(branch_slugs),
                "firefox-version": json.dumps(targets),
                "server": server,
            },
        }

        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code != 204:
            raise KlaatuError(
                f"Failed to trigger workflow. URL: {url}",
                status_code=response.status_code,
                response_text=response.text,
            )

    def find_run_ids(
        self, experiment_slug: str, dispatched_at: Optional[datetime.datetime] = None
    ) -> list[int]:
        run_ids = set()
        query = {"event": "workflow_dispatch"}
        if dispatched_at:
            query["created"] = f">={dispatched_at.isoformat()}Z"

        path = KlaatuEndpoints.RUNS.format(workflow=self.workflow_name)
        base_url = urljoin(self.base_url, path)
        url = f"{base_url}?{urlencode(query)}"

        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise KlaatuError(
                "Failed to fetch workflow runs",
                status_code=response.status_code,
                response_text=response.text,
            )

        workflow_runs = response.json().get("workflow_runs", [])
        for run in workflow_runs:
            if experiment_slug in run.get("display_title", ""):
                run_ids.add(int(run["id"]))
        return list(run_ids)

    def is_job_complete(self, job_id: int) -> bool:
        path = KlaatuEndpoints.RUN_STATUS.format(run_id=str(job_id))
        url = urljoin(self.base_url, path)

        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            status = response.json()["status"]
            return status == KlaatuStatus.COMPLETE
        raise KlaatuError(
            "Failed to check job status",
            status_code=response.status_code,
            response_text=response.text,
        )

    def fetch_artifacts(self, job_id: int) -> dict[str, str]:
        path = KlaatuEndpoints.ARTIFACTS.format(run_id=str(job_id))
        artifacts_url = urljoin(self.base_url, path)

        response = requests.get(artifacts_url, headers=self.headers)
        if response.status_code != 200:
            raise KlaatuError(
                "Failed to get artifacts",
                status_code=response.status_code,
                response_text=response.text,
            )

        artifacts = response.json().get("artifacts", [])
        if not artifacts:
            raise KlaatuError(f"No artifact found for job {job_id}")

        result = {}

        for artifact in artifacts:
            download_url = artifact.get("archive_download_url", "")

            download_response = requests.get(download_url, headers=self.headers)
            if download_response.status_code != 200:
                raise KlaatuError(
                    "Failed to download artifact",
                    status_code=download_response.status_code,
                    response_text=download_response.text,
                )

            with zipfile.ZipFile(io.BytesIO(download_response.content)) as zip_file:
                for name in zip_file.namelist():
                    if name.endswith(".html"):
                        with zip_file.open(name, "r") as file:
                            result[artifact["name"]] = file.read().decode("utf-8")

        return result
