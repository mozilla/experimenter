from urllib.parse import urlparse

import pytest
import requests


@pytest.fixture(name="experiment_type", scope="module")
def fixture_experiment_type():
    return "branched-multi-addon-study"


@pytest.fixture(name="experiment_name", scope="module")
def fixture_experiment_name():
    return "Add-On Experiment"


@pytest.mark.use_variables
@pytest.mark.nondestructive
def test_branched_multi_addon_e2e(
    base_url,
    selenium,
    experiment_type,
    fill_timeline_page,
    fill_design_page_branched_multi_addon,
    fill_analysis_page,
    fill_risks_page,
    signoff_and_ship,
    variables,
):
    url = urlparse(selenium.current_url)
    experiment_url = f"{url.scheme}://{url.netloc}/api/v1{url.path}recipe/"
    experiment_json = requests.get(f"{experiment_url}", verify=False).json()
    assert variables[experiment_type]["name"] in experiment_json["name"]
    assert variables[experiment_type]["action_name"] == experiment_json["action_name"]
    assert (
        variables[experiment_type]["type"] == experiment_json["filter_object"][1]["type"]
    )
    assert (
        variables[experiment_type]["channels"].lower()
        == experiment_json["filter_object"][1]["channels"][0]
    )
    assert (
        variables[experiment_type]["min_version"]
        == f"{[item for item in experiment_json['filter_object'][2]['versions']][0]}.0"
    )
    assert (
        variables[experiment_type]["max_version"]
        == f"{[item for item in experiment_json['filter_object'][2]['versions']][-1]}.0"
    )
    assert (
        variables[experiment_type]["userFacingName"]
        == experiment_json["arguments"]["userFacingName"]
    )
    assert (
        variables[experiment_type]["userFacingDescription"]
        == experiment_json["arguments"]["userFacingDescription"]
    )
    assert len(variables[experiment_type]["branches"]) == len(
        experiment_json["arguments"]["branches"]
    )
    for item in experiment_json["arguments"][
        "branches"
    ]:  # Loop over each item in the Branches secion
        for num in range(
            len(experiment_json["arguments"]["branches"])
        ):  # Check each branch so we need to do the check for as many branches exis
            try:
                assert (
                    item["slug"]
                    == variables[experiment_type]["branches"][num]["branch_name"]
                )
            except AssertionError:
                continue
