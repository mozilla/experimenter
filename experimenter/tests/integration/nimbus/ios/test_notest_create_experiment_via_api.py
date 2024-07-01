import logging
import os
from pathlib import Path
import json

import pytest
import requests

from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.utils import helpers


@pytest.fixture
def experiment_slug():
    return "firefox-ios-integration-test4"


# @pytest.fixture(name="write_recipe_json")
# def fixture_write_recipe_json():
#     def _write_recipe_json(recipe):
#         here = Path(__file__)
#         recipe_file = here / "recipe.json"
#         recipe_file.write_text(json.dumps(recipe))
#         yield
#         recipe_file.unlink()
#     return _write_recipe_json

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

def test_create_ios_experiment_for_integration_test(
    selenium,
    experiment_url,
    kinto_client,
    base_url,
    application,
    default_data_api,
    experiment_slug,
    tmpdir,
):
    # status = helpers.create_experiment(
    #     experiment_slug,
    #     BaseExperimentApplications.FIREFOX_IOS.value,
    #     default_data_api
    # )
    # logging.info(status)

    # summary = SummaryPage(selenium, experiment_url).open()
    # summary.launch_and_approve()

    # kinto_client.approve()

    # SummaryPage(selenium, experiment_url, timeout=120).open().wait_for_live_status()

    recipe = requests.get(f"https://nginx/api/v6/experiments/{experiment_slug}/", verify=False).json()
    path = Path(tmpdir)
    json_file = path / "recipe.json"
    json_file.write_text(json.dumps(recipe))
    logging.info(json_file)
    os.environ["IOS_RECIPE_FILE"] = str(json_file.absolute())
    logging.info(os.environ["IOS_RECIPE_FILE"])
