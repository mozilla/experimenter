import re
import subprocess
import time
from pathlib import Path

import pytest

NIMBUS_CLI_APP = "firefox_ios"
BUNDLE_ID = "org.mozilla.ios.Fennec"
LOG_POLL_DEADLINE_SECONDS = 180
LOG_POLL_INTERVAL_SECONDS = 2


@pytest.mark.ios_enrollment
def test_ios_enrollment(ios_channel, ios_app_path, ios_recipe, ios_recipe_path):
    experiment_slug = ios_recipe["slug"]
    subprocess.check_call(["xcrun", "simctl", "install", "booted", ios_app_path])
    subprocess.check_call(
        [
            "nimbus-cli",
            "--app",
            NIMBUS_CLI_APP,
            "--channel",
            ios_channel,
            "enroll",
            experiment_slug,
            "--branch",
            "control",
            "--file",
            str(ios_recipe_path),
            "--preserve-targeting",
            "--preserve-bucketing",
            "--reset-app",
            "--no-validate",
        ]
    )

    container = subprocess.check_output(
        ["xcrun", "simctl", "get_app_container", "booted", BUNDLE_ID, "data"],
        text=True,
    ).strip()
    log_path = Path(container) / "Library" / "Caches" / "Logs" / "Firefox.log"
    pattern = re.compile(rf"{re.escape(experiment_slug)}\s*\|\s*\S+\s*\|\s*(\S+)")
    deadline = time.time() + LOG_POLL_DEADLINE_SECONDS
    while time.time() < deadline:
        if log_path.exists():
            match = pattern.search(log_path.read_text())
            if match:
                assert match.group(1).strip() in {"control", "treatment-a"}
                return
        time.sleep(LOG_POLL_INTERVAL_SECONDS)
    pytest.fail(f"No enrollment row for {experiment_slug}")
