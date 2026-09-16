import json
from pathlib import Path
from tempfile import TemporaryDirectory

import responses
from django.core.management import call_command
from django.test import TestCase, override_settings

from experimenter.addons import NEWTAB_ADDON, VERSIONS_FILENAME, Addons
from experimenter.addons.management.commands.fetch_addon_versions import (
    MANIFEST_ARTIFACT_PATH,
    SHIPIT_API_URL,
    TASKCLUSTER_API_URL,
)

EXISTING_VERSION = {
    "version": "158.0.20260913.220257",
    "shipit_release": "newtab-158.0.0-build1",
    "xpi_revision": "9779d0c588762208f33a82c9fc710f81466f6e9e",
    "created": "2026-09-13T21:47:36.718463Z",
}


def release(name, action_task_id="action-task-id", xpi_revision="deadbeef"):
    return {
        "name": name,
        "xpi_version": "145.0.0",
        "created": "2025-09-19T17:18:18.203037Z",
        "xpi_revision": xpi_revision,
        "phases": [
            {"name": "ship", "actionTaskId": "ship-task-id"},
            {"name": "build", "actionTaskId": action_task_id},
        ],
    }


def release_without_build_phase(name):
    return {
        "name": name,
        "xpi_version": "145.0.0",
        "created": "2025-09-19T17:18:18.203037Z",
        "xpi_revision": "deadbeef",
        "phases": [{"name": "build", "actionTaskId": None}],
    }


def task(name, task_id):
    return {"status": {"taskId": task_id}, "task": {"metadata": {"name": name}}}


def mock_releases(releases):
    responses.get(f"{SHIPIT_API_URL}xpi/releases", json=releases)


def mock_task_group(action_task_id, tasks):
    responses.get(
        f"{TASKCLUSTER_API_URL}queue/v1/task-group/{action_task_id}/list",
        json={"tasks": tasks},
    )


def mock_manifest(build_task_id, version=None, status=200):
    responses.get(
        f"{TASKCLUSTER_API_URL}queue/v1/task/{build_task_id}/artifacts/"
        f"{MANIFEST_ARTIFACT_PATH}",
        json={"version": version} if version else {},
        status=status,
    )


class TestFetchAddonVersions(TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.addCleanup(Addons.clear_cache)

        self.versions_path = Path(self.temp_dir.name) / "versions"
        self.versions_path.mkdir()
        self.override = override_settings(ADDON_VERSIONS_PATH=self.versions_path)
        self.override.enable()
        self.addCleanup(self.override.disable)

        Addons.clear_cache()

    def write_committed(self, addon, versions):
        addon_path = self.versions_path / addon
        addon_path.mkdir(exist_ok=True)
        (addon_path / VERSIONS_FILENAME).write_text(json.dumps(versions))
        Addons.clear_cache()

    def read_committed(self, addon):
        return json.loads((self.versions_path / addon / VERSIONS_FILENAME).read_text())

    @responses.activate
    def test_known_releases_make_no_taskcluster_requests(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_releases([release(EXISTING_VERSION["shipit_release"])])

        call_command("fetch_addon_versions")

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(self.read_committed(NEWTAB_ADDON), [EXISTING_VERSION])

    @responses.activate
    def test_new_release_is_merged_and_sorted(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_releases(
            [
                release(EXISTING_VERSION["shipit_release"]),
                release("newtab-145.0.0-build1", xpi_revision="4d5eae1e"),
            ]
        )
        mock_task_group(
            "action-task-id",
            [
                task("dep-signing-newtab", "signing-task-id"),
                task("build-newtab", "build-task-id"),
            ],
        )
        mock_manifest("build-task-id", version="145.0.20250919.173227")

        call_command("fetch_addon_versions")

        self.assertEqual(
            self.read_committed(NEWTAB_ADDON),
            [
                {
                    "version": "145.0.20250919.173227",
                    "shipit_release": "newtab-145.0.0-build1",
                    "xpi_revision": "4d5eae1e",
                    "created": "2025-09-19T17:18:18.203037Z",
                },
                EXISTING_VERSION,
            ],
        )

    @responses.activate
    def test_addon_directory_is_created_when_absent(self):
        mock_releases([release("newtab-145.0.0-build1")])
        mock_task_group("action-task-id", [task("build-newtab", "build-task-id")])
        mock_manifest("build-task-id", version="145.0.20250919.173227")

        call_command("fetch_addon_versions")

        self.assertEqual(
            [version["version"] for version in self.read_committed(NEWTAB_ADDON)],
            ["145.0.20250919.173227"],
        )

    @responses.activate
    def test_untracked_addon_versions_are_left_alone(self):
        tabtweak_version = {
            "version": "3.1.20260401.120000",
            "shipit_release": "tabtweak-3.1.0-build1",
            "xpi_revision": "0f1e2d3c",
            "created": "2026-04-01T11:45:00Z",
        }
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        self.write_committed("tabtweak", [tabtweak_version])
        mock_releases([release(EXISTING_VERSION["shipit_release"])])

        call_command("fetch_addon_versions")

        self.assertEqual(self.read_committed("tabtweak"), [tabtweak_version])
        self.assertEqual(self.read_committed(NEWTAB_ADDON), [EXISTING_VERSION])

    @responses.activate
    def test_new_release_with_expired_artifact_is_skipped(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_releases([release("newtab-159.0.0-build1")])
        mock_task_group("action-task-id", [task("build-newtab", "build-task-id")])
        mock_manifest("build-task-id", status=404)

        call_command("fetch_addon_versions")

        self.assertEqual(self.read_committed(NEWTAB_ADDON), [EXISTING_VERSION])

    @responses.activate
    def test_committed_version_survives_its_artifact_expiring(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_releases(
            [
                release(
                    EXISTING_VERSION["shipit_release"],
                    action_task_id="expired-action-task-id",
                ),
                release("newtab-159.0.0-build1", xpi_revision="cafebabe"),
            ]
        )
        mock_task_group(
            "expired-action-task-id", [task("build-newtab", "expired-build-task-id")]
        )
        mock_manifest("expired-build-task-id", status=404)
        mock_task_group("action-task-id", [task("build-newtab", "build-task-id")])
        mock_manifest("build-task-id", version="159.0.20260920.120000")

        call_command("fetch_addon_versions")

        self.assertEqual(
            [version["version"] for version in self.read_committed(NEWTAB_ADDON)],
            ["158.0.20260913.220257", "159.0.20260920.120000"],
        )

    @responses.activate
    def test_release_without_build_task_is_skipped(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_releases([release("newtab-159.0.0-build1")])
        mock_task_group(
            "action-task-id", [task("release-notify-newtab", "notify-task-id")]
        )

        call_command("fetch_addon_versions")

        self.assertEqual(self.read_committed(NEWTAB_ADDON), [EXISTING_VERSION])

    @responses.activate
    def test_release_without_build_phase_makes_no_taskcluster_requests(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_releases([release_without_build_phase("newtab-159.0.0-build1")])

        call_command("fetch_addon_versions")

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(self.read_committed(NEWTAB_ADDON), [EXISTING_VERSION])

    @responses.activate
    def test_written_file_is_reloaded_by_the_cached_accessor(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        Addons.all()
        mock_releases([release("newtab-159.0.0-build1")])
        mock_task_group("action-task-id", [task("build-newtab", "build-task-id")])
        mock_manifest("build-task-id", version="159.0.20260920.120000")

        call_command("fetch_addon_versions")

        self.assertEqual(
            [version.version for version in Addons.by_addon(NEWTAB_ADDON)],
            ["158.0.20260913.220257", "159.0.20260920.120000"],
        )
