from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from experimenter.addons import (
    NEWTAB_ADDON,
    VERSIONS_FILENAME,
    Addons,
    AddonVersion,
    AddonVersions,
)

TASKCLUSTER_API_URL = "https://firefox-ci-tc.services.mozilla.com/api/"
MANIFEST_ARTIFACT_PATH = "public%2Fbuild%2Fmanifest.json"
RELEASE_SIGNING_INDEX_NAMESPACE = "xpi.v2.xpi-manifest.{addon}.release-signing.revision"
ACTION_TASK_NAME_PREFIX = "Action:"
INDEX_TASKS_LIMIT = 1000
REQUEST_TIMEOUT = 60
TRACKED_ADDONS = (NEWTAB_ADDON,)


class Command(BaseCommand):
    help = (
        "Merge newly shipped addon versions from the Taskcluster index "
        "into the committed versions"
    )

    def handle(self, *args, **options):
        for addon in TRACKED_ADDONS:
            versions = list(Addons.by_addon(addon))
            known_revisions = {version.xpi_revision for version in versions}

            for revision, signing_task_id in self.fetch_signed_revisions(addon):
                if revision in known_revisions:
                    continue

                version = self.fetch_version(addon, signing_task_id)

                if version is None:
                    self.stdout.write(
                        f"No build manifest available for {addon} revision "
                        f"{revision}, skipping"
                    )
                    continue

                versions.append(version)
                self.stdout.write(f"Added {addon} version {version.version}")

            versions.sort(key=lambda version: version.sort_key)
            self.write_versions(addon, versions)

        Addons.clear_cache()

    def write_versions(self, addon, versions):
        addon_path = settings.ADDON_VERSIONS_PATH / addon
        addon_path.mkdir(parents=True, exist_ok=True)

        with (addon_path / VERSIONS_FILENAME).open("w") as versions_file:
            versions_file.write(AddonVersions(root=versions).model_dump_json(indent=2))
            versions_file.write("\n")

    def fetch_signed_revisions(self, addon):
        namespace = RELEASE_SIGNING_INDEX_NAMESPACE.format(addon=addon)
        url = urljoin(TASKCLUSTER_API_URL, f"index/v1/tasks/{namespace}")
        payload = {"limit": INDEX_TASKS_LIMIT}

        while True:
            response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            body = response.json()

            for task in body["tasks"]:
                yield task["namespace"].rsplit(".", 1)[-1], task["taskId"]

            continuation_token = body.get("continuationToken")

            if not continuation_token:
                return

            payload = {
                "limit": INDEX_TASKS_LIMIT,
                "continuationToken": continuation_token,
            }

    def fetch_version(self, addon, signing_task_id):
        signing_task = self.fetch_task(signing_task_id)
        build_task_id = None
        action_task = None

        for dependency_id in signing_task["dependencies"]:
            dependency = self.fetch_task(dependency_id)
            name = dependency["metadata"]["name"]

            if name == f"build-{addon}":
                build_task_id = dependency_id
            elif name.startswith(ACTION_TASK_NAME_PREFIX):
                action_task = dependency

        if build_task_id is None or action_task is None:
            return None

        manifest = self.fetch_build_manifest(build_task_id)

        if manifest is None:
            return None

        action_input = action_task["extra"]["action"]["context"]["input"]

        return AddonVersion(
            version=manifest["version"],
            shipit_release=(
                f"{action_input['xpi_name']}-{action_input['version']}"
                f"-build{action_input['build_number']}"
            ),
            xpi_revision=action_input["revision"],
            created=action_task["created"],
        )

    def fetch_task(self, task_id):
        response = requests.get(
            urljoin(TASKCLUSTER_API_URL, f"queue/v1/task/{task_id}"),
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def fetch_build_manifest(self, build_task_id):
        response = requests.get(
            urljoin(
                TASKCLUSTER_API_URL,
                f"queue/v1/task/{build_task_id}/artifacts/{MANIFEST_ARTIFACT_PATH}",
            ),
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == requests.codes.not_found:
            return None

        response.raise_for_status()
        return response.json()
