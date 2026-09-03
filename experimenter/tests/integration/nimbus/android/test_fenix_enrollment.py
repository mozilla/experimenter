import json
import re
import subprocess
import time

import pytest

from nimbus.models.base_dataclass import BaseExperimentApplications

FENIX_APP = BaseExperimentApplications.FIREFOX_FENIX.value
ENROLL_TIMEOUT = 120
ENROLL_POLL_INTERVAL = 5


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

    # Prevent the real Nimbus RS fetch from overwriting our local enrollment
    # (without this, Nimbus evolves against the fresh fetch — which does not
    # contain our test experiment — and unenrolls us).
    subprocess.check_call(
        ["adb", "shell", "cmd", "connectivity", "airplane-mode", "enable"]
    )

    def enroll():
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

    pattern = re.compile(
        rf"nimbus_client:\s*{re.escape(experiment_slug)}\s+\|\s*\S+\s+\|\s*(\S+)"
    )

    logcat = ""
    match = None
    deadline = time.monotonic() + ENROLL_TIMEOUT
    while time.monotonic() < deadline:
        subprocess.check_call(["adb", "logcat", "-c"])
        enroll()
        time.sleep(ENROLL_POLL_INTERVAL)
        logcat = subprocess.check_output(["adb", "logcat", "-d"], text=True)
        match = pattern.search(logcat)
        if match is not None:
            break

    nimbus_lines = [line for line in logcat.splitlines() if "nimbus_client" in line]
    assert match is not None, (
        f"No enrollment row found for {experiment_slug} after {ENROLL_TIMEOUT}s.\n"
        f"--- last 30 nimbus_client lines ---\n" + "\n".join(nimbus_lines[-30:])
    )
    enrolled_branch = match.group(1)
    assert enrolled_branch in {"control", "treatment-a"}, (
        f"Unexpected branch {enrolled_branch!r} for {experiment_slug}"
    )
