# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import os
from pathlib import Path
import subprocess

import pytest
import requests

from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.utils import helpers
from xcodebuild import XCodeBuild
from xcrun import XCRun


here = Path(__file__)


@pytest.fixture(name="nimbus_cli_args")
def fixture_nimbus_cli_args():
    return "FIREFOX_SKIP_INTRO FIREFOX_TEST DISABLE_ANIMATIONS 'GCDWEBSERVER_PORT:7777'"


@pytest.fixture()
def xcodebuild_log(request, tmp_path_factory):
    xcodebuild_log = tmp_path_factory.mktemp("logs") / "xcodebuild.log"
    logging.info(f"Logs stored at: {xcodebuild_log}")
    request.config._xcodebuild_log = xcodebuild_log
    yield xcodebuild_log


@pytest.fixture(scope="session", autouse=True)
def fixture_build_fennec(request):
    if not request.config.getoption("--build-dev"):
        return
    command = "xcodebuild build-for-testing -project Client.xcodeproj -scheme Fennec -configuration Fennec -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 15,OS=17.2'"
    try:
        logging.info("Building app")
        subprocess.check_output(
            command,
            cwd=here.parents[2],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True)
    except subprocess.CalledProcessError:
        raise


@pytest.fixture()
def xcodebuild(xcodebuild_log):
    yield XCodeBuild(xcodebuild_log, scheme="Fennec", test_plan="ExperimentIntegrationTests")


@pytest.fixture(scope="session")
def xcrun():
    return XCRun()


@pytest.fixture(name="device_control", scope="module", autouse=True)
def fixture_device_control(xcrun):
    xcrun.boot()
    yield
    xcrun.erase()
    

@pytest.fixture(name="start_app")
def fixture_start_app(nimbus_cli_args):
    def _():
        command = f"nimbus-cli --app firefox_ios --channel developer open -- {nimbus_cli_args}"
        out = subprocess.check_output(
            command,
            cwd=here.parent,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True,
        )
        logging.debug(out)

    return _


# @pytest.fixture(name="json_data")
# def fixture_json_data(tmp_path, experiment_data):
#     path = tmp_path / "data"
#     path.mkdir()
#     json_path = path / "data.json"
#     with open(json_path, "w", encoding="utf-8") as f:
#         # URL of experiment/klaatu server
#         data = {"data": experiment_data}
#         json.dump(data, f)
#     return json_path


@pytest.fixture(name="set_env_variables", autouse=True)
def fixture_set_env_variables(experiment_data):
    """Set any env variables XCUITests might need"""
    os.environ["EXPERIMENT_NAME"] = experiment_data[0]["userFacingName"]


@pytest.fixture
def experiment_slug():
    return "firefox-ios-integration-test4"


@pytest.fixture
def default_data_api(application, application_feature_ids):
    feature_config_id = application_feature_ids[application]
    return {
        "hypothesis": "Test Hypothesis",
        "application": application,
        "changelogMessage": "test updates",
        "targetingConfigSlug": "no_targeting",
        "publicDescription": "Some sort of Fancy Words",
        "riskRevenue": False,
        "riskPartnerRelated": False,
        "riskBrand": False,
        "riskMessage": False,
        "featureConfigIds": [int(feature_config_id)],
        "referenceBranch": {
            "description": "reference branch",
            "name": "Branch 1",
            "ratio": 50,
            "featureValues": [
                {
                    "featureConfig": str(feature_config_id),
                    "value": "{}",
                },
            ],
        },
        "treatmentBranches": [],
        "populationPercent": "100",
        "totalEnrolledClients": 55,
        "firefoxMinVersion": "FIREFOX_120",
    }


@pytest.fixture(name="create_and_approve_experiment")
def fixture_create_and_approve_experiment(
    selenium,
    experiment_url,
    kinto_client,
    default_data_api,
):
    def _create_and_approve_experiment():
        status = helpers.create_experiment(
            experiment_slug,
            BaseExperimentApplications.FIREFOX_IOS.value,
            default_data_api
        )
        logging.info(status)

        summary = SummaryPage(selenium, experiment_url).open()
        summary.launch_and_approve()

        kinto_client.approve()

        SummaryPage(selenium, experiment_url, timeout=120).open().wait_for_live_status()
    return _create_and_approve_experiment


@pytest.fixture(name="setup_experiment")
def setup_experiment(experiment_slug, experiment_branch, nimbus_cli_args, tmpdir, create_and_approve_experiment):
    def _setup_experiment():
        # Create experiment and return it's json
        create_and_approve_experiment()
        recipe = requests.get(f"https://nginx/api/v6/experiments/{experiment_slug}/", verify=False).json()
        path = Path(tmpdir)
        json_file = path / "recipe.json"
        json_file.write_text(json.dumps(recipe))
        logging.info(json_file)
        os.environ["IOS_RECIPE_FILE"] = str(json_file.absolute())
        logging.info(os.environ["IOS_RECIPE_FILE"])

        logging.info(f"Testing experiment {experiment_slug}, BRANCH: {experiment_branch}")
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
            f"{json_file}"
            "--reset-app",
            "--",
            f"{nimbus_cli_args}" 
        ]
        logging.info(f"Nimbus CLI Command: {command}\n")
        out = subprocess.check_output(
            " ".join(command),
            cwd=os.path.join(here, os.pardir),
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True,
        )   

    return _setup_experiment
