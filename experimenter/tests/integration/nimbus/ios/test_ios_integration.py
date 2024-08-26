import logging
import os
import subprocess
import time
from pathlib import Path

import pytest

here = Path(__file__)


@pytest.fixture
def experiment_slug():
    return "firefox-ios-integration-test-experiment"


@pytest.fixture(name="device_control", scope="module", autouse=True)
def fixture_device_control(xcrun):
    ...  # Overriding for Experimenter Integration Test


@pytest.fixture(name="experiment_url", scope="module")
def fixture_experiment_url(request, variables):
    ...  # Overriding for Experimenter Integration Test


@pytest.fixture(name="experiment_data")
def fixture_experiment_data(experiment_url, request):
    ...  # Overriding for Experimenter Integration Test


@pytest.fixture(name="set_env_variables", autouse=True)
def fixture_set_env_variables(experiment_slug):
    """Set any env variables XCUITests might need"""
    os.environ["EXPERIMENT_NAME"] = experiment_slug


@pytest.fixture(name="setup_experiment")
def setup_experiment(experiment_slug, nimbus_cli_args):
    def _setup_experiment():
        logging.info(f"Testing experiment {experiment_slug}")
        command = [
            "nimbus-cli",
            "--app",
            "firefox_ios",
            "--channel",
            "developer",
            "enroll",
            f"{experiment_slug}",
            "--branch",
            "control",
            "--file",
            "/tmp/experimenter/tests/integration/ios_recipe.json",
            "--reset-app",
            "--",
            f"{nimbus_cli_args}",
        ]
        logging.info(f"Nimbus CLI Command: {' '.join(command)}")
        out = subprocess.check_output(
            " ".join(command),
            cwd=here.parent,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True,
        )
        logging.info(out)

    return _setup_experiment


@pytest.mark.ios_enrollment
def test_experiment_unenrolls_after_studies_toggle(
    xcodebuild, setup_experiment, start_app
):
    xcodebuild.install(boot=False)
    xcodebuild.test(
        "XCUITests/ExperimentIntegrationTests/testAppStartup", build=False, erase=False
    )
    setup_experiment()
    time.sleep(5)
    xcodebuild.test(
        "XCUITests/ExperimentIntegrationTests/testVerifyExperimentEnrolled",
        build=False,
        erase=False,
    )
    start_app()
    xcodebuild.test(
        "XCUITests/ExperimentIntegrationTests/testStudiesToggleDisablesExperiment",
        build=False,
        erase=False,
    )
