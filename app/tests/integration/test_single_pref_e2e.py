import json
from urllib.parse import urlparse

import pytest
import requests

experiment_type = "single-pref-experiment"


@pytest.mark.use_variables
@pytest.mark.nondestructive
def test_single_pref_e2e(
    base_url,
    selenium,
    fill_timeline_page,
    fill_design_page_single_pref,
    fill_analysis_page,
    fill_risks_page,
    signoff_and_ship,
):
    url = urlparse(selenium.current_url)
    experiment_url = f"{url.scheme}://{url.netloc}/api/v1{url.path}recipe/"
    experiment_json = requests.get(f"{experiment_url}", verify=False).json()
    with open("e2e_test_variables.json", "r") as j:
        test_json = json.load(j)
    assert test_json["single-pref-experiment"]["name"] in experiment_json["name"]
    assert (
        test_json["single-pref-experiment"]["action_name"]
        == experiment_json["action_name"]
    )
    assert (
        test_json["single-pref-experiment"]["type"]
        == experiment_json["filter_object"][1]["type"]
    )
    assert (
        test_json["single-pref-experiment"]["channels"].lower()
        == experiment_json["filter_object"][1]["channels"][0]
    )
    assert (
        test_json["single-pref-experiment"]["min_version"]
        == f"{[item for item in experiment_json['filter_object'][2]['versions']][0]}.0"
    )
    assert (
        test_json["single-pref-experiment"]["max_version"]
        == f"{[item for item in experiment_json['filter_object'][2]['versions']][-1]}.0"
    )
    assert (
        test_json["single-pref-experiment"]["userFacingName"]
        == experiment_json["arguments"]["userFacingName"]
    )
    assert (
        test_json["single-pref-experiment"]["userFacingDescription"]
        == experiment_json["arguments"]["userFacingDescription"]
    )
    assert len(test_json["single-pref-experiment"]["branches"]) == len(
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
                == test_json["single-pref-experiment"]["branches"][num]["branch_name"]
            ):  # Start by checking the name
                assert (
                    test_json["single-pref-experiment"]["branches"][num][
                        "firefox_pref_name"
                    ]
                    in f"{[key for key in item['preferences']]}"
                )
                assert (
                    test_json["single-pref-experiment"]["branches"][num][
                        "firefox_pref_type"
                    ]
                    in f"{[value['preferenceType'] for value in item['preferences'].values()]}"  # noqa: E501
                )
                assert (
                    test_json["single-pref-experiment"]["branches"][num][
                        "firefox_pref_branch"
                    ]
                    in f"{[value['preferenceBranchType'] for value in item['preferences'].values()]}"  # noqa: E501
                )
                assert (
                    test_json["single-pref-experiment"]["branches"][num]["branch_value"]
                    in f"{[value['preferenceValue'] for value in item['preferences'].values()]}".lower()  # noqa: E501
                )
