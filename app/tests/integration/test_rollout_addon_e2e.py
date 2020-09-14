from urllib.parse import urlparse

import pytest
import requests
from models.base_dataclass import (
    BaseBranchDataClass,
    BaseDataClass,
    BasePreferencesDataClass,
)
from models.validation_dataclass import APIDataClass


@pytest.fixture(name="experiment_type", scope="module")
def fixture_experiment_type():
    return "addon-rollout"


@pytest.fixture(name="experiment_name", scope="module")
def fixture_experiment_name():
    return "Staged Rollout"


@pytest.fixture(name="default_data", scope="module")
def fixture_default_data(experiment_name, experiment_type):
    branches = []
    preferences = [
        BasePreferencesDataClass(
            preference_branch_name="e2e-testing",
            preference_branch_type="default",
            preference_type="boolean",
            preference_value="true",
        ),
    ]

    branches.append(
        BaseBranchDataClass(
            addon_url="http://addon.com/addon.xpi",
            branch_name="e2e-rollout-branch-0",
            preferences=preferences,
        )
    )

    return BaseDataClass(
        type_name=experiment_name,
        action_name=experiment_type,
        experiment_type="channel",
        channels="Nightly",
        min_version=99,
        max_version=100,
        user_facing_name="e2e testing rollout pref experiment",
        user_facing_description="e2e testing rollout pref description",
        branches=sorted(branches, key=lambda x: x.branch_name),
    )


@pytest.mark.use_variables
@pytest.mark.nondestructive
def test_addon_rollout_experiment_e2e(
    base_url,
    selenium,
    experiment_type,
    fill_timeline_page_pref_rollout,
    fill_design_page_addon_rollout,
    fill_analysis_page,
    fill_risks_page,
    signoff_and_ship,
    variables,
    default_data,
):
    url = urlparse(selenium.current_url)
    experiment_url = f"{url.scheme}://{url.netloc}/api/v1{url.path}recipe/"
    experiment_json = requests.get(experiment_url, verify=False).json()
    api_json = APIDataClass(**experiment_json)
    assert default_data.action_name == api_json.action_name
    assert default_data.experiment_type == api_json.filter_object[1].type
    assert default_data.channels.lower() in api_json.filter_object[1].channels
    assert default_data.min_version == api_json.filter_object[2].versions[0]
    assert default_data.max_version == api_json.filter_object[2].versions[-1]
    assert default_data.branches[0].addon_url in api_json.arguments.extensionApiId
