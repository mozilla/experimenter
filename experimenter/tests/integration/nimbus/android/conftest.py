# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os
import subprocess
import time
from pathlib import Path

import pytest
import requests

from .gradlewbuild import GradlewBuild
from .models.models import TelemetryModel

here = Path().cwd()


def start_process(path, command):
    module_path = Path(path)

    try:
        process = subprocess.Popen(
            command,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=module_path.absolute(),
        )
        stdout, stderr = process.communicate(timeout=5)

        if process.returncode != 0:
            raise Exception(stderr)
    except subprocess.TimeoutExpired:
        logging.info(f"{module_path.name} started")
        return process


@pytest.fixture(name="run_nimbus_cli_command")
def fixture_run_nimbus_cli_command(gradlewbuild_log):
    def _run_nimbus_cli_command(command):
        logging.info(f"Running command {command}")
        try:
            out = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            out = e.output
            raise
        finally:
            with Path.open(gradlewbuild_log, "w") as f:
                f.write(f"{out}")

    return _run_nimbus_cli_command


@pytest.fixture(name="open_app")
def fixture_open_app(run_nimbus_cli_command):
    def _():
        command = "nimbus-cli --app fenix --channel developer open"
        run_nimbus_cli_command(command)
        time.sleep(10)

    return _


@pytest.fixture
def gradlewbuild_log(pytestconfig, tmpdir):
    gradlewbuild_log = f"{tmpdir.join('gradlewbuild.log')}"
    pytestconfig._gradlewbuild_log = gradlewbuild_log
    yield gradlewbuild_log


@pytest.fixture
def gradlewbuild(gradlewbuild_log):
    yield GradlewBuild(gradlewbuild_log)


@pytest.fixture(name="ping_server", autouse=True, scope="session")
def fixture_ping_server():
    path = next(iter(here.glob("**/android/ping_server")))
    process = start_process(path, ["python", "ping_server.py"])
    yield "http://localhost:5000"
    process.terminate()


@pytest.fixture(name="delete_telemetry_pings")
def fixture_delete_telemetry_pings(ping_server):
    def runner():
        requests.delete(f"{ping_server}/pings")

    return runner


@pytest.fixture(name="check_ping_for_experiment")
def fixture_check_ping_for_experiment(experiment_slug, ping_server, open_app):
    def _check_ping_for_experiment(branch=None, experiment=experiment_slug, reason=None):
        model = TelemetryModel(branch=branch, experiment=experiment)

        timeout = time.time() + 60
        while time.time() < timeout:
            data = requests.get(f"{ping_server}/pings").json()
            events = []
            for item in data:
                event_items = item.get("events")
                if event_items:
                    for event in event_items:
                        if (
                            "category" in event
                            and "nimbus_events" in event["category"]
                            and "extra" in event
                            and "branch" in event["extra"]
                        ):
                            events.append(event)
            for event in events:
                event_name = event.get("name")
                if (reason == "enrollment" and event_name == "enrollment") or (
                    reason == "unenrollment"
                    and event_name in ["unenrollment", "disqualification"]
                ):
                    telemetry_model = TelemetryModel(
                        branch=event["extra"]["branch"],
                        experiment=event["extra"]["experiment"],
                    )
                    if model == telemetry_model:
                        return True
            time.sleep(5)
            open_app()  # Open app in cycles to trigger telemetry
        return False

    return _check_ping_for_experiment


@pytest.fixture(name="set_experiment_test_name", autouse=True, scope="session")
def fixture_set_experiment_test_name():
    os.environ["EXP_NAME"] = "fenix"


@pytest.fixture(name="setup_experiment")
def fixture_setup_experiment(
    run_nimbus_cli_command,
    delete_telemetry_pings,
):
    def _():
        experiment_json = next(iter(here.glob("**/fixtures/experiment.json")))
        delete_telemetry_pings()
        logging.info("Testing fenix e2e experiment")
        command = f"nimbus-cli --app fenix --channel developer enroll firefox-fenix-test-experiment --branch control --file {experiment_json} --reset-app"  #  NOQA
        run_nimbus_cli_command(command)
        time.sleep(
            15
        )  # Wait a while as there's no real way to know when the app has started

    return _
