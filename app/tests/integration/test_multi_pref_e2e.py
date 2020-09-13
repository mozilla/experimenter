from urllib.parse import urlparse

import pytest
import requests
from models.base_dataclass import (
    BaseBranchDataClass,
    BaseDataClass,
    BasePreferencesDataClass
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
            preference_branch_name="e2e-testing-branch-1",
            preference_branch_type="default",
            preference_type="boolean",
            preference_value="true",
        ),
        BasePreferencesDataClass(
            preference_branch_name="e2e-testing-branch-1-1",
            preference_branch_type="default",
            preference_type="integer",
            preference_value="10",
        ),
        BasePreferencesDataClass(
            preference_branch_name="e2e-testing-branch-2",
            preference_branch_type="default",
            preference_type="string",
            preference_value="pref-string",
        ),
        BasePreferencesDataClass(
            preference_branch_name="e2e-testing-branch-2-1",
            preference_branch_type="default",
            preference_type="json string",
            preference_value='{"object": "name"}',
        ),
    ]

    branches = [
        BaseBranchDataClass(
            branch_name="e2e-singlepref-branch",
            branch_description="multipref-branch-description",
            preferences=sorted(preferences[:-2], key=lambda x: x.preference_branch_name),
        ),
        BaseBranchDataClass(
            branch_name="e2e-singlepref-branch-2",
            branch_description="multipref-branch-description",
            preferences=sorted(preferences[-2:], key=lambda x: x.preference_branch_name),
        ),
    ]

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
def test_multi_pref_e2e(
    base_url,
    selenium,
    experiment_type,
    fill_timeline_page,
    fill_design_page_multi_prefs,
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
    assert default_data.user_facing_name in api_json.name
    assert default_data.action_name == api_json.action_name
    assert default_data.experiment_type == api_json.filter_object[1].type
    assert default_data.channels.lower() in api_json.filter_object[1].channels
    assert default_data.min_version == api_json.filter_object[2].versions[0]
    assert default_data.max_version == api_json.filter_object[2].versions[-1]
    assert (
        default_data.user_facing_description in api_json.arguments.userFacingDescription
    )
    assert len(default_data.branches) == len(api_json.arguments.branches)
    default_branches = {branch.branch_name: branch for branch in default_data.branches}
    for api_branch in sorted(api_json.arguments.branches, key=lambda x: x.slug):
        assert api_branch.slug in default_branches
        default_branch = default_branches[api_branch.slug]
        for item in default_branch.preferences:
            pref_data = api_branch.preferences.get(item.preference_branch_name)
            assert pref_data.preferenceType in item.preference_type
            assert pref_data.preferenceBranchType == item.preference_branch_type
            assert str(pref_data.preferenceValue).lower() in item.preference_value
