import json
from urllib.parse import urlparse

import pytest
import requests

experiment_type = "branched-multi-addon-study"
experiment_type_name = "Add-On Experiment"


@pytest.mark.use_variables
@pytest.mark.nondestructive
def test_branched_multi_addon_e2e(
    base_url,
    selenium,
    fill_timeline_page,
    fill_design_page_branched_multi_addon,
    fill_analysis_page,
    fill_risks_page,
    signoff_and_ship,
):
    url = urlparse(selenium.current_url)
    experiment_url = f"{url.scheme}://{url.netloc}/api/v1{url.path}recipe/"
    experiment_json = requests.get(f"{experiment_url}", verify=False).json()
    with open("e2e_test_variables.json", "r") as j:
        test_json = json.load(j)
    assert test_json[experiment_type]["name"] in experiment_json["name"]
    assert test_json[experiment_type]["action_name"] == experiment_json["action_name"]
    assert (
        test_json[experiment_type]["type"] == experiment_json["filter_object"][1]["type"]
    )
    assert (
        test_json[experiment_type]["channels"].lower()
        == experiment_json["filter_object"][1]["channels"][0]
    )
    assert (
        test_json[experiment_type]["min_version"]
        == f"{[item for item in experiment_json['filter_object'][2]['versions']][0]}.0"
    )
    assert (
        test_json[experiment_type]["max_version"]
        == f"{[item for item in experiment_json['filter_object'][2]['versions']][-1]}.0"
    )
    assert (
        test_json[experiment_type]["userFacingName"]
        == experiment_json["arguments"]["userFacingName"]
    )
    assert (
        test_json[experiment_type]["userFacingDescription"]
        == experiment_json["arguments"]["userFacingDescription"]
    )
    assert len(test_json[experiment_type]["branches"]) == len(
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
                    == test_json[experiment_type]["branches"][num]["branch_name"]
                )
            except AssertionError:
                continue
