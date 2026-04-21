import json
import re
import subprocess
import time

import pytest

from nimbus.models.base_dataclass import BaseExperimentApplications

FENIX_APP = BaseExperimentApplications.FIREFOX_FENIX.value
APP_APPLY_WAIT = 15
LOG_STATE_WAIT = 5


@pytest.mark.fenix_enrollment
def test_fenix_enrollment(
    fenix_channel,
    fenix_apk_path,
    experiment_slug,
    create_fenix_experiment,
    tmp_path,
):
    recipe = create_fenix_experiment(experiment_slug, fenix_channel)

    recipe_path = tmp_path / "fenix_recipe.json"
    recipe_path.write_text(json.dumps(recipe))

    subprocess.check_call(["adb", "install", fenix_apk_path])
    subprocess.check_call(["adb", "logcat", "-c"])

    # Prevent the real Nimbus RS fetch from overwriting our local enrollment
    # (without this, Nimbus evolves against the fresh fetch — which does not
    # contain our test experiment — and unenrolls us).
    subprocess.check_call(["adb", "shell", "svc", "wifi", "disable"])
    subprocess.check_call(["adb", "shell", "svc", "data", "disable"])

    subprocess.check_call(
        [
            "nimbus-cli",
            "--app",
            FENIX_APP,
            "--channel",
            fenix_channel,
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
        ["nimbus-cli", "--app", FENIX_APP, "--channel", fenix_channel, "log-state"]
    )
    time.sleep(LOG_STATE_WAIT)

    logcat = subprocess.check_output(["adb", "logcat", "-d"], text=True)

    pattern = re.compile(
        rf"nimbus_client:\s*{re.escape(experiment_slug)}\s+\|\s*\S+\s+\|\s*(\S+)"
    )
    match = pattern.search(logcat)
    nimbus_lines = [line for line in logcat.splitlines() if "nimbus_client" in line]
    assert match is not None, (
        f"No log-state row found for {experiment_slug}.\n"
        f"--- last 30 nimbus_client lines ---\n" + "\n".join(nimbus_lines[-30:])
    )
    enrolled_branch = match.group(1)
    assert enrolled_branch in {"control", "treatment-a"}, (
        f"Unexpected branch {enrolled_branch!r} for {experiment_slug}"
    )
