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

SHIPIT_API_URL = "https://shipit-api.mozilla-releng.net/"
TASKCLUSTER_API_URL = "https://firefox-ci-tc.services.mozilla.com/api/"
MANIFEST_ARTIFACT_PATH = "public%2Fbuild%2Fmanifest.json"
BUILD_PHASE_NAME = "build"
BUILD_TASK_NAME_PREFIX = "build-"
REQUEST_TIMEOUT = 60
TASK_GROUP_LIMIT = 200
RELEASES_LIMIT = 500
TRACKED_ADDONS = (NEWTAB_ADDON,)


class Command(BaseCommand):
    help = "Merge newly shipped addon versions from ShipIt into the committed versions"

    def handle(self, *args, **options):
        for addon in TRACKED_ADDONS:
            versions = list(Addons.by_addon(addon))
            known_releases = {version.shipit_release for version in versions}

            for release in self.fetch_releases(addon):
                if release["name"] in known_releases:
                    continue

                version = self.fetch_version(release)

                if version is None:
                    self.stdout.write(
                        f"No build manifest available for {release['name']}, skipping"
                    )
                    continue

                versions.append(
                    AddonVersion(
                        version=version,
                        shipit_release=release["name"],
                        xpi_revision=release["xpi_revision"],
                        created=release["created"],
                    )
                )
                self.stdout.write(f"Added {addon} version {version}")

            versions.sort(key=lambda version: version.sort_key)
            self.write_versions(addon, versions)

        Addons.clear_cache()

    def write_versions(self, addon, versions):
        addon_path = settings.ADDON_VERSIONS_PATH / addon
        addon_path.mkdir(parents=True, exist_ok=True)

        with (addon_path / VERSIONS_FILENAME).open("w") as versions_file:
            versions_file.write(AddonVersions(root=versions).model_dump_json(indent=2))
            versions_file.write("\n")

    def fetch_releases(self, addon):
        response = requests.get(
            urljoin(SHIPIT_API_URL, "xpi/releases"),
            params={
                "xpi_name": addon,
                "status": "shipped",
                "limit": RELEASES_LIMIT,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def fetch_version(self, release):
        action_task_id = self.build_action_task_id(release)
        if action_task_id is None:
            return None

        build_task_id = self.fetch_build_task_id(action_task_id)
        if build_task_id is None:
            return None

        manifest = self.fetch_build_manifest(build_task_id)
        if manifest is None:
            return None

        return manifest["version"]

    def build_action_task_id(self, release):
        for phase in release["phases"]:
            if phase["name"] == BUILD_PHASE_NAME and phase.get("actionTaskId"):
                return phase["actionTaskId"]
        return None

    def fetch_build_task_id(self, action_task_id):
        response = requests.get(
            urljoin(TASKCLUSTER_API_URL, f"queue/v1/task-group/{action_task_id}/list"),
            params={"limit": TASK_GROUP_LIMIT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        for task in response.json()["tasks"]:
            if task["task"]["metadata"]["name"].startswith(BUILD_TASK_NAME_PREFIX):
                return task["status"]["taskId"]
        return None

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
