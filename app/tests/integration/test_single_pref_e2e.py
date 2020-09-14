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
    return "multi-preference-experiment"


@pytest.fixture(name="experiment_name", scope="module")
def fixture_experiment_name():
    return "Pref-Flip Experiment"


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
        BasePreferencesDataClass(
            preference_branch_name="e2e-testing",
            preference_branch_type="default",
            preference_type="boolean",
            preference_value="false",
        ),
    ]

    for count, item in enumerate(preferences):
        branches.append(
            BaseBranchDataClass(
                branch_name=f"e2e-singlepref-branch-{count}", preferences=item
            )
        )

    return BaseDataClass(
        type_name=experiment_name,
        action_name=experiment_type,
        experiment_type="channel",
        channels="Nightly",
        min_version=99,
        max_version=100,
        user_facing_name="e2e testing name",
        user_facing_description="e2e testing description",
        branches=sorted(branches, key=lambda x: x.branch_name),
    )


@pytest.mark.use_variables
@pytest.mark.nondestructive
def test_single_pref_e2e(
    base_url,
    selenium,
    experiment_type,
    fill_timeline_page,
    fill_design_page_single_pref,
    fill_analysis_page,
    fill_risks_page,
    signoff_and_ship,
    variables,
    default_data,
):
    url = urlparse(selenium.current_url)
    experiment_url = f"{url.scheme}://{url.netloc}/api/v1{url.path}recipe/"
    experiment_json = requests.get(f"{experiment_url}", verify=False).json()
    api_json = APIDataClass(**experiment_json)
    assert default_data.action_name == api_json.action_name
    assert default_data.experiment_type == api_json.filter_object[1].type
    assert default_data.channels.lower() in api_json.filter_object[1].channels
    assert default_data.min_version == api_json.filter_object[2].versions[0]
    assert default_data.max_version == api_json.filter_object[2].versions[-1]
    assert default_data.user_facing_name in api_json.arguments.userFacingName
    assert (
        default_data.user_facing_description in api_json.arguments.userFacingDescription
    )
    assert len(default_data.branches) == len(api_json.arguments.branches)
    for count, data in enumerate(default_data.branches):
        api_branches = sorted(api_json.arguments.branches, key=lambda x: x.slug)
        branch_name, api_preferences = list(api_branches[count].preferences.items())[-1]
        assert data.preferences.preference_branch_name in branch_name
        assert data.preferences.preference_type == api_preferences.preferenceType
        assert (
            data.preferences.preference_branch_type
            == api_preferences.preferenceBranchType
        )
        assert (
            data.preferences.preference_value
            in str(api_preferences.preferenceValue).lower()
        )
