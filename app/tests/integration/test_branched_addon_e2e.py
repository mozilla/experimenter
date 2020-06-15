from urllib.parse import urlparse

import pytest
import requests

from models.validation_json import JsonData
from models.base_json import BaseBranchData, BaseJsonData


@pytest.fixture(name="experiment_type", scope="module")
def fixture_experiment_type():
    return "branched-single-addon-study"


@pytest.fixture(name="experiment_name", scope="module")
def fixture_experiment_name():
    return "Add-On Experiment"


@pytest.fixture(name="default_data", scope="module")
def fixture_default_data():
    branches = []
    preferences = [None, None]

    for count, item in enumerate(preferences):
        branches.append(
            BaseBranchData(
                branch_name=f"e2e-addon-branch-{count}",
                branch_description="e2e Branch Description",
                preferences=item,
            )
        )

    return BaseJsonData(
        type_name="Add-On Experiment",
        action_name="branched-addon-study",
        addon_url="https://url.com/addon-url.xpi",
        experiment_type="channel",
        channels="Nightly",
        min_version=99,
        max_version=100,
        user_facing_name="e2e testing addon name",
        user_facing_description="e2e testing addon description",
        branches=sorted(branches, key=lambda x: x.branch_name),
    )


@pytest.mark.use_variables
@pytest.mark.nondestructive
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
    api_json = JsonData(**experiment_json)
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
    api_branches = sorted(api_json.arguments.branches, key=lambda x: x.slug)
    for count, data in enumerate(default_data.branches):
        assert default_data.branches[count].branch_name == api_branches[count].slug
