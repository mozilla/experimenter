import io
import json
import zipfile

import requests
from django.conf import settings


class KlaatuClient:
    def __init__(self, workflow_name):
        self.workflow_name = workflow_name
        self.auth_token = settings.GITHUB_AUTH_TOKEN
        self.base_url = "https://api.github.com/repos/mozilla/klaatu"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    def run_test(self, experiment_slug, branch_slug, targets):
        url = f"{self.base_url}/actions/workflows/{self.workflow_name}/dispatches"

        data = {
            "ref": "main",
            "inputs": {
                "slug": experiment_slug,
                "branch": json.dumps([branch_slug]),
                "firefox-version": json.dumps(targets),
            },
        }

        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code != 204:
            raise Exception(
                f"Failed to trigger workflow: {response.status_code}, {response.text}"
            )

    def find_run_id(self, experiment_slug, dispatched_at=None):
        created_filter = ""
        if dispatched_at:
            created_filter = f"&created=>={dispatched_at.isoformat()}Z"

        url = (
            f"{self.base_url}/actions/workflows/{self.workflow_name}/runs"
            f"?event=workflow_dispatch{created_filter}"
        )

        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch workflow runs: {response.status_code}, {response.text}"
            )

        workflow_runs = response.json().get("workflow_runs", [])
        for run in workflow_runs:
            if experiment_slug in run.get("display_title", ""):
                return run["id"]

    def is_job_complete(self, job_id):
        url = f"{self.base_url}/actions/runs/{job_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            status = response.json()["status"]
            return status == "completed"
        raise Exception(
            f"Failed to check job status: {response.status_code}, {response.text}"
        )

    def download_artifact(self, job_id):
        artifacts_url = f"{self.base_url}/actions/runs/{job_id}/artifacts"

        response = requests.get(artifacts_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(
                f"Failed to get artifacts: {response.status_code}, {response.text}"
            )

        artifacts = response.json().get("artifacts", [])
        if not artifacts:
            raise Exception(f"No artifact found for job {job_id}")

        for artifact in artifacts:
            download_url = artifact["archive_download_url"]

            download_response = requests.get(download_url, headers=self.headers)
            if download_response.status_code != 200:
                raise Exception(
                    f"Failed to download artifact: {download_response.status_code}, "
                    f"{download_response.text}"
                )

            with zipfile.ZipFile(io.BytesIO(download_response.content)) as zip_file:
                zip_file.extractall(
                    f"experimenter/experimenter/klaatu/reports/{job_id}/{artifact['name']}.html"
                )
