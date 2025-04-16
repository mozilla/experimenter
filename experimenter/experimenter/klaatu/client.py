import json
import time
import requests
import datetime
import zipfile
import io
from django.conf import settings

class KlaatuClient:
    def __init__(self, workflow_name):
        self.workflow_name = workflow_name
        self.auth_token=settings.GITHUB_AUTH_TOKEN
        self.base_url = f"https://api.github.com/repos/mozilla/klaatu"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    def run_test(self, experiment_slug, branch_slug, targets):
        url = f"{self.base_url}/actions/workflows/{self.workflow_name}/dispatches"
        before_dispatch_time = datetime.datetime.utcnow().isoformat() + "Z"

        data = {
            "ref": "main",
            "inputs": {
                "slug": experiment_slug,
                "branch": json.dumps([branch_slug]),
                "firefox-version": json.dumps(targets)
            }
        }

        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code != 204:
            raise Exception(f"Failed to trigger workflow: {response.status_code}, {response.text}")

        runs_url = (
            f"{self.base_url}/actions/workflows/{self.workflow_name}/runs"
            f"?event=workflow_dispatch&created=>={before_dispatch_time}"
        )

        timeout = 30
        elapsed = 0
        while elapsed < timeout:
            runs_response = requests.get(runs_url, headers=self.headers)
            if runs_response.status_code == 200:
                workflow_runs = runs_response.json().get("workflow_runs", [])
                for run in workflow_runs:
                    if experiment_slug in run.get("display_title", ""):
                        return run["id"]
            time.sleep(3)
            elapsed += 3

        raise Exception("Could not find the workflow run.")

    def is_job_complete(self, job_id):
        url = f"{self.base_url}/actions/runs/{job_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            status = response.json()["status"]
            return status == "completed"
        raise Exception(f"Failed to check job status: {response.status_code}, {response.text}")

    def download_artifact(self, job_id):
        artifacts_url = f"{self.base_url}/actions/artifacts"

        response = requests.get(artifacts_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get artifacts: {response.status_code}, {response.text}")

        artifacts = response.json().get("artifacts", [])
        matching_artifacts = [a for a in artifacts if a["workflow_run"]["id"] == job_id]

        if not matching_artifacts:
            raise Exception(f"No artifact found for job {job_id}")

        for artifact in matching_artifacts:
            download_url = artifact["archive_download_url"]

            download_response = requests.get(download_url, headers=self.headers)
            if download_response.status_code != 200:
                raise Exception(f"Failed to download artifact: {download_response.status_code}, {download_response.text}")

            with zipfile.ZipFile(io.BytesIO(download_response.content)) as zip_file:
                zip_file.extractall(f"experimenter/experimenter/klaatu/reports/{job_id}/{artifact['name']}.html")
