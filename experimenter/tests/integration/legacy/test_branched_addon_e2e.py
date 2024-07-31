from urllib.parse import urlparse

import pytest
import requests
from models.base_dataclass import BaseBranchDataClass, BaseDataClass
from models.validation_dataclass import APIDataClass


@pytest.fixture(name="experiment_type", scope="module")
def fixture_experiment_type():
    return "branched-addon-study"


@pytest.fixture(name="experiment_name", scope="module")
def fixture_experiment_name():
    return "Add-On Experiment"


@pytest.fixture(name="default_data", scope="module")
def fixture_default_data(experiment_name, experiment_type):
    preferences = [None, None]

    branches = [
        BaseBranchDataClass(
            branch_name=f"e2e-addon-branch-{count}",
            branch_description="e2e Branch Description",
            preferences=item,
        )
        for count, item in enumerate(preferences)
    ]
    return BaseDataClass(
        type_name=experiment_name,
        action_name=experiment_type,
        addon_url="https://url.com/addon-url.xpi",
        experiment_type="channel",
        channels="Nightly",
        min_version=98,
        max_version=99,
        user_facing_name="e2e testing addon name",
        user_facing_description="e2e testing addon description",
        branches=sorted(branches, key=lambda x: x.branch_name),
    )


@pytest.mark.use_variables
@pytest.mark.nondestructive
@pytest.mark.skip(reason="intermittently failing")
def test_branched_addon_e2e(
    base_url,
    selenium,
    experiment_type,
    fill_timeline_page,
    fill_design_page_branched_single_addon,
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
    default_branches = {branch.branch_name: branch for branch in default_data.branches}
    for api_branch in sorted(api_json.arguments.branches, key=lambda x: x.slug):
        assert api_branch.slug in default_branches
