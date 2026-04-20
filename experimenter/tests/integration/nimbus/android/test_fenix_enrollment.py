import json
import os
import re
import subprocess
import time
from pathlib import Path

import pytest
import requests

from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.utils import helpers

FENIX_APP = BaseExperimentApplications.FIREFOX_FENIX.value
RECIPE_POLL_TIMEOUT = 60
APP_APPLY_WAIT = 15
LOG_STATE_WAIT = 5


@pytest.fixture
def channel():
    value = os.environ.get("FENIX_CHANNEL")
    if not value:
        pytest.skip("FENIX_CHANNEL is not set")
    return value


@pytest.fixture
def apk_path():
    value = os.environ.get("FENIX_APK_PATH")
    if not value or not Path(value).exists():
        pytest.skip(f"FENIX_APK_PATH not set or missing: {value!r}")
    return value


@pytest.fixture
def experiment_slug(channel):
    return f"fenix-{channel}-integration-test"


def _mint_preview_experiment(slug, channel, feature_id):
    helpers.create_experiment(
        slug,
        FENIX_APP,
        data={
            "feature_config_ids": [int(feature_id)],
            "reference_branch": {
                "name": "control",
                "description": "control branch",
            },
            "population_percent": "100",
            "total_enrolled_clients": "1000000",
            "channel": channel,
            "firefox_min_version": "",
        },
        targeting="no_targeting",
    )
    helpers._post_form(f"/nimbus/{slug}/draft-to-preview/")


def _wait_for_recipe(slug):
    url = f"{helpers._get_nginx_url()}/api/v6/experiments/{slug}/"
    deadline = time.time() + RECIPE_POLL_TIMEOUT
    last_error = None
    while time.time() < deadline:
        try:
            resp = requests.get(url, verify=False, timeout=5)
            if resp.status_code == 200:
                recipe = resp.json()
                if recipe.get("slug") == slug and recipe.get("bucketConfig"):
                    return recipe
                last_error = (
                    f"recipe missing bucketConfig: {recipe.get('bucketConfig')!r}"
                )
            else:
                last_error = f"HTTP {resp.status_code}"
        except (requests.RequestException, ValueError) as exc:
            last_error = str(exc)
        time.sleep(1)
    pytest.fail(f"Timed out waiting for recipe at {url} ({last_error})")


@pytest.mark.fenix_enrollment
def test_fenix_enrollment(
    channel, apk_path, experiment_slug, application_feature_ids, tmp_path
):
    feature_id = application_feature_ids[FENIX_APP]
    assert feature_id, f"No feature id registered for '{FENIX_APP}'"
    _mint_preview_experiment(experiment_slug, channel, feature_id)
    recipe = _wait_for_recipe(experiment_slug)

    recipe_path = tmp_path / "fenix_recipe.json"
    recipe_path.write_text(json.dumps(recipe))

    subprocess.check_call(["adb", "install", "-r", "-t", "-g", apk_path])
    subprocess.check_call(["adb", "logcat", "-c"])

    subprocess.check_call(
        [
            "nimbus-cli",
            "--app",
            FENIX_APP,
            "--channel",
            channel,
            "enroll",
            experiment_slug,
            "--branch",
            "control",
            "--file",
            str(recipe_path),
            "--preserve-targeting",
            "--preserve-bucketing",
            "--reset-app",
            "--no-validate",
        ]
    )
    time.sleep(APP_APPLY_WAIT)

    subprocess.check_call(
        ["nimbus-cli", "--app", FENIX_APP, "--channel", channel, "log-state"]
    )
    time.sleep(LOG_STATE_WAIT)

    logcat = subprocess.check_output(["adb", "logcat", "-d"], text=True)

    pattern = re.compile(
        rf"nimbus_client:\s*{re.escape(experiment_slug)}\s+\|\s*\S+\s+\|\s*(\S+)"
    )
    match = pattern.search(logcat)
    if match is None:
        nimbus_lines = [line for line in logcat.splitlines() if "nimbus_client" in line]
        assert match is not None, (
            f"No log-state row found for {experiment_slug}.\n"
            f"--- last 30 nimbus_client lines ---\n" + "\n".join(nimbus_lines[-30:])
        )
    enrolled_branch = match.group(1)
    assert enrolled_branch in {"control", "treatment-a"}, (
        f"Unexpected branch {enrolled_branch!r} for {experiment_slug}"
    )
