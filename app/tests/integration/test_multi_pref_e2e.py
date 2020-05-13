import json
from urllib.parse import urlparse

import pytest
import requests

experiment_type = "multi-pref-experiment"


@pytest.mark.use_variables
@pytest.mark.multi_prefs
@pytest.mark.nondestructive
def test_multi_pref_e2e(base_url, selenium, fill_experiment):
    url = urlparse(selenium.current_url)
    experiment_url = f"{url.scheme}://{url.netloc}/api/v1{url.path}recipe/"
    experiment_json = requests.get(f"{experiment_url}", verify=False).json()
    with open("e2e_test_variables.json", "r") as j:
        test_json = json.load(j)
    assert test_json["multi-pref-experiment"]["name"] in experiment_json["name"]
    assert (
        test_json["multi-pref-experiment"]["action_name"]
        == experiment_json["action_name"]
    )
    assert (
        test_json["multi-pref-experiment"]["type"]
        == experiment_json["filter_object"][1]["type"]
    )
    assert (
        test_json["multi-pref-experiment"]["channels"].lower()
        == experiment_json["filter_object"][1]["channels"][0]
    )
    assert (
        test_json["multi-pref-experiment"]["min_version"]
        == f"{[item for item in experiment_json['filter_object'][2]['versions']][0]}.0"
    )
    assert (
        test_json["multi-pref-experiment"]["max_version"]
        == f"{[item for item in experiment_json['filter_object'][2]['versions']][-1]}.0"
    )
    assert (
        test_json["multi-pref-experiment"]["userFacingName"]
        == experiment_json["arguments"]["userFacingName"]
    )
    assert (
        test_json["multi-pref-experiment"]["userFacingDescription"]
        == experiment_json["arguments"]["userFacingDescription"]
    )
    assert len(test_json["multi-pref-experiment"]["branches"]) == len(
        experiment_json["arguments"]["branches"]
    )
    for item in experiment_json["arguments"][
        "branches"
    ]:  # Loop over each item in the Branches secion
        for num in range(
            len(experiment_json["arguments"]["branches"])
        ):  # Check each branch so we need to do the check for as many branches exis
            if (
                item["slug"]
                == test_json["multi-pref-experiment"]["branches"][num]["branch_name"]
            ):  # Start by checking the name
                for pref_num in range(len(item["preferences"])):
                    assert (
                        test_json["multi-pref-experiment"]["branches"][num][
                            "preferences"
                        ][pref_num]["firefox_pref_name"]
                        in f"{[key for key in item['preferences']]}"
                    )
                    assert (
                        test_json["multi-pref-experiment"]["branches"][num][
                            "preferences"
                        ][pref_num]["firefox_pref_type"]
                        in f"{[value['preferenceType'] for value in item['preferences'].values()]}"  # noqa: E501
                    )
                    assert (
                        test_json["multi-pref-experiment"]["branches"][num][
                            "preferences"
                        ][pref_num]["firefox_pref_branch"]
                        in f"{[value['preferenceBranchType'] for value in item['preferences'].values()]}"  # noqa: E501
                    )
                    assert (
                        test_json["multi-pref-experiment"]["branches"][num][
                            "preferences"
                        ][pref_num]["firefox_pref_value"]
                        in f"{[value['preferenceValue'] for value in item['preferences'].values()]}".lower()  # noqa: E501
                    )
