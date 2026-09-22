import json
from pathlib import Path
from tempfile import TemporaryDirectory

import responses
from django.core.management import call_command
from django.test import TestCase, override_settings

from experimenter.addons import NEWTAB_ADDON, VERSIONS_FILENAME, Addons
from experimenter.addons.management.commands.fetch_addon_versions import (
    MANIFEST_ARTIFACT_PATH,
    RELEASE_SIGNING_INDEX_NAMESPACE,
    TASKCLUSTER_API_URL,
)

INDEX_NAMESPACE = RELEASE_SIGNING_INDEX_NAMESPACE.format(addon=NEWTAB_ADDON)

EXISTING_VERSION = {
    "version": "158.0.20260913.220257",
    "shipit_release": "newtab-158.0.0-build1",
    "xpi_revision": "9779d0c588762208f33a82c9fc710f81466f6e9e",
    "created": "2026-09-13T21:47:36.718463Z",
}


def index_task(revision, task_id):
    return {
        "namespace": f"{INDEX_NAMESPACE}.{revision}",
        "taskId": task_id,
        "rank": 0,
        "data": {},
        "expires": "2027-08-24T08:50:39.238Z",
    }


def mock_index(tasks, continuation_token=None):
    body = {"tasks": tasks}

    if continuation_token:
        body["continuationToken"] = continuation_token

    responses.post(
        f"{TASKCLUSTER_API_URL}index/v1/tasks/{INDEX_NAMESPACE}",
        json=body,
    )


def mock_task(task_id, body):
    responses.get(f"{TASKCLUSTER_API_URL}queue/v1/task/{task_id}", json=body)


def mock_signing_task(task_id, dependencies):
    mock_task(
        task_id,
        {
            "metadata": {"name": f"release-signing-{NEWTAB_ADDON}"},
            "dependencies": dependencies,
        },
    )


def mock_build_task(task_id):
    mock_task(task_id, {"metadata": {"name": f"build-{NEWTAB_ADDON}"}})


def mock_other_task(task_id):
    mock_task(task_id, {"metadata": {"name": f"release-notify-{NEWTAB_ADDON}"}})


def mock_action_task(task_id, version, revision, created, build_number=1):
    mock_task(
        task_id,
        {
            "metadata": {"name": "Action: Promote an XPI"},
            "created": created,
            "extra": {
                "action": {
                    "context": {
                        "input": {
                            "xpi_name": NEWTAB_ADDON,
                            "version": version,
                            "build_number": build_number,
                            "revision": revision,
                            "release_promotion_flavor": "ship",
                        }
                    }
                }
            },
        },
    )


def mock_manifest(build_task_id, version=None, status=200):
    responses.get(
        f"{TASKCLUSTER_API_URL}queue/v1/task/{build_task_id}/artifacts/"
        f"{MANIFEST_ARTIFACT_PATH}",
        json={"version": version} if version else {},
        status=status,
    )


def mock_release(revision, version, created, manifest_version=None, manifest_status=200):
    signing_task_id = f"signing-task-id-{revision}"
    build_task_id = f"build-task-id-{revision}"
    action_task_id = f"action-task-id-{revision}"

    mock_signing_task(signing_task_id, [build_task_id, action_task_id])
    mock_build_task(build_task_id)
    mock_action_task(action_task_id, version, revision, created)
    mock_manifest(build_task_id, version=manifest_version, status=manifest_status)

    return index_task(revision, signing_task_id)


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
    def test_known_revisions_make_no_queue_requests(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_index([index_task(EXISTING_VERSION["xpi_revision"], "signing-task-id")])

        call_command("fetch_addon_versions")

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(self.read_committed(NEWTAB_ADDON), [EXISTING_VERSION])

    @responses.activate
    def test_new_release_is_merged_and_sorted(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_index(
            [
                index_task(EXISTING_VERSION["xpi_revision"], "known-signing-task-id"),
                mock_release(
                    "4d5eae1eccb3b383b4a251a679a821012307daa7",
                    "145.0.0",
                    "2025-09-19T17:18:18.203037Z",
                    manifest_version="145.0.20250919.173227",
                ),
            ]
        )

        call_command("fetch_addon_versions")

        self.assertEqual(
            self.read_committed(NEWTAB_ADDON),
            [
                {
                    "version": "145.0.20250919.173227",
                    "shipit_release": "newtab-145.0.0-build1",
                    "xpi_revision": "4d5eae1eccb3b383b4a251a679a821012307daa7",
                    "created": "2025-09-19T17:18:18.203037Z",
                },
                EXISTING_VERSION,
            ],
        )

    @responses.activate
    def test_addon_directory_is_created_when_absent(self):
        mock_index(
            [
                mock_release(
                    "4d5eae1eccb3b383b4a251a679a821012307daa7",
                    "145.0.0",
                    "2025-09-19T17:18:18.203037Z",
                    manifest_version="145.0.20250919.173227",
                )
            ]
        )

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
        mock_index([index_task(EXISTING_VERSION["xpi_revision"], "signing-task-id")])

        call_command("fetch_addon_versions")

        self.assertEqual(self.read_committed("tabtweak"), [tabtweak_version])
        self.assertEqual(self.read_committed(NEWTAB_ADDON), [EXISTING_VERSION])

    @responses.activate
    def test_new_release_with_expired_artifact_is_skipped(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_index(
            [
                mock_release(
                    "7a3b5c91",
                    "159.0.0",
                    "2026-09-20T12:00:00Z",
                    manifest_status=404,
                )
            ]
        )

        call_command("fetch_addon_versions")

        self.assertEqual(self.read_committed(NEWTAB_ADDON), [EXISTING_VERSION])

    @responses.activate
    def test_release_without_build_task_is_skipped(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_signing_task("signing-task-id", ["notify-task-id", "action-task-id"])
        mock_other_task("notify-task-id")
        mock_action_task("action-task-id", "159.0.0", "7a3b5c91", "2026-09-20T12:00:00Z")
        mock_index([index_task("7a3b5c91", "signing-task-id")])

        call_command("fetch_addon_versions")

        self.assertEqual(self.read_committed(NEWTAB_ADDON), [EXISTING_VERSION])

    @responses.activate
    def test_release_without_action_task_is_skipped(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_signing_task("signing-task-id", ["build-task-id"])
        mock_build_task("build-task-id")
        mock_index([index_task("7a3b5c91", "signing-task-id")])

        call_command("fetch_addon_versions")

        self.assertEqual(self.read_committed(NEWTAB_ADDON), [EXISTING_VERSION])

    @responses.activate
    def test_index_pagination_follows_the_continuation_token(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_index(
            [index_task(EXISTING_VERSION["xpi_revision"], "known-signing-task-id")],
            continuation_token="next-page",
        )
        mock_index(
            [
                mock_release(
                    "7a3b5c91",
                    "159.0.0",
                    "2026-09-20T12:00:00Z",
                    manifest_version="159.0.20260920.120000",
                )
            ]
        )

        call_command("fetch_addon_versions")

        self.assertEqual(
            [version["version"] for version in self.read_committed(NEWTAB_ADDON)],
            ["158.0.20260913.220257", "159.0.20260920.120000"],
        )
        self.assertEqual(
            json.loads(responses.calls[1].request.body),
            {"limit": 1000, "continuationToken": "next-page"},
        )

    @responses.activate
    def test_committed_version_survives_an_absent_index_entry(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        mock_index(
            [
                mock_release(
                    "7a3b5c91",
                    "159.0.0",
                    "2026-09-20T12:00:00Z",
                    manifest_version="159.0.20260920.120000",
                )
            ]
        )

        call_command("fetch_addon_versions")

        self.assertEqual(
            self.read_committed(NEWTAB_ADDON),
            [
                EXISTING_VERSION,
                {
                    "version": "159.0.20260920.120000",
                    "shipit_release": "newtab-159.0.0-build1",
                    "xpi_revision": "7a3b5c91",
                    "created": "2026-09-20T12:00:00Z",
                },
            ],
        )

    @responses.activate
    def test_written_file_is_reloaded_by_the_cached_accessor(self):
        self.write_committed(NEWTAB_ADDON, [EXISTING_VERSION])
        Addons.all()
        mock_index(
            [
                mock_release(
                    "7a3b5c91",
                    "159.0.0",
                    "2026-09-20T12:00:00Z",
                    manifest_version="159.0.20260920.120000",
                )
            ]
        )

        call_command("fetch_addon_versions")

        self.assertEqual(
            [version.version for version in Addons.by_addon(NEWTAB_ADDON)],
            ["158.0.20260913.220257", "159.0.20260920.120000"],
        )
