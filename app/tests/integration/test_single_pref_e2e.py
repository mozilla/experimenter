from urllib.parse import urlparse

import pytest
import requests


@pytest.fixture(name="experiment_type", scope="module")
def fixture_experiment_type():
    return "single-pref-experiment"


@pytest.fixture(name="experiment_name", scope="module")
def fixture_experiment_name():
    return "Pref-Flip Experiment"


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
):
    url = urlparse(selenium.current_url)
    experiment_url = f"{url.scheme}://{url.netloc}/api/v1{url.path}recipe/"
    experiment_json = requests.get(f"{experiment_url}", verify=False).json()
    assert variables[experiment_type]["userFacingName"] in experiment_json["name"]
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
        in experiment_json["arguments"]["userFacingName"]
    )
    assert (
        variables[experiment_type]["userFacingDescription"]
        == experiment_json["arguments"]["userFacingDescription"]
    )
    assert len(variables[experiment_type]["branches"]) == len(
        experiment_json["arguments"]["branches"]
    )
    for item in experiment_json["arguments"]["branches"]:
        for num in range(len(experiment_json["arguments"]["branches"])):
            if item["slug"] == variables[experiment_type]["branches"][num]["branch_name"]:
                assert (
                    variables[experiment_type]["branches"][num]["firefox_pref_name"]
                    in f"{[key for key in item['preferences']]}"
                )
                assert (
                    variables[experiment_type]["branches"][num]["firefox_pref_type"]
                    in f"{[value['preferenceType'] for value in item['preferences'].values()]}"  # noqa: E501
                )
                assert (
                    variables[experiment_type]["branches"][num]["firefox_pref_branch"]
                    in f"{[value['preferenceBranchType'] for value in item['preferences'].values()]}"  # noqa: E501
                )
                assert (
                    variables[experiment_type]["branches"][num]["branch_value"]
                    in f"{[value['preferenceValue'] for value in item['preferences'].values()]}".lower()  # noqa: E501
                )
