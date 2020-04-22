import datetime
from dateutil.parser import parse
from urllib.parse import urlparse
import json

import pytest
import requests

from pages.home import Home
from pages.experiment_timeline_and_population import TimelineAndPopulationPage
from pages.experiment_design import DesignPage
from pages.experiment_objective_and_analysis import ObjectiveAndAnalysisPage


@pytest.fixture
def fill_timeline(base_url, selenium, variables, ds_issue_host):
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    experiment.name = f"{variables['multi-pref-experiment']['name']}"
    experiment.short_description = "Testing in here"
    experiment.public_name = f"{variables['multi-pref-experiment']['userFacingName']}"
    experiment.public_description = (
        f"{variables['multi-pref-experiment']['userFacingDescription']}"
    )
    experiment.ds_issue_url = f"{ds_issue_host}DS-12345"
    selenium.find_element_by_id("save-and-continue-btn").click()
    # Fill timeline page
    timeline = TimelineAndPopulationPage(selenium, base_url).wait_for_page_to_load()
    date = f"{datetime.datetime.now()}"
    new_date = parse(date)
    today = f"{new_date.date()}"
    timeline.proposed_start_date = today
    timeline.proposed_experiment_duration = "25"
    timeline.population_precentage = "100.0"
    timeline.firefox_channel = f"{variables['multi-pref-experiment']['channels']}"
    timeline.firefox_min_version = f"{variables['multi-pref-experiment']['min_version']}"
    timeline.firefox_max_version = f"{variables['multi-pref-experiment']['max_version']}"
    selenium.find_element_by_id("save-and-continue-btn").click()
    # Fill design page
    design = DesignPage(selenium, base_url).wait_for_page_to_load()
    design.input_firefox_pref_name(
        f"{variables['multi-pref-experiment']['branches'][0]['firefox_pref_name']}"
    )
    design.select_firefox_pref_type(
        f"{variables['multi-pref-experiment']['branches'][0]['firefox_pref_type']}"
    )
    design.select_firefox_pref_branch(
        f"{variables['multi-pref-experiment']['branches'][0]['firefox_pref_branch']}"
    )
    current_branchs = design.current_branches
    control_branch = current_branchs[0]
    control_branch.set_branch_name(
        f"{variables['multi-pref-experiment']['branches'][0]['branch_name']}"
    )
    control_branch.set_branch_description("THIS IS A TEST")
    control_branch.set_branch_value(
        f"{variables['multi-pref-experiment']['branches'][0]['branch_value']}"
    )
    current_branchs[1].set_branch_name(
        f"{variables['multi-pref-experiment']['branches'][1]['branch_name']}"
    )
    current_branchs[1].set_branch_description("THIS IS A TEST")
    current_branchs[1].set_branch_value(
        f"{variables['multi-pref-experiment']['branches'][1]['branch_value']}"
    )
    design.save_and_continue()
    # selenium.find_element_by_css_selector("btn-primary").click()
    analysis_page = ObjectiveAndAnalysisPage(selenium, base_url).wait_for_page_to_load()
    analysis_page.objectives_text_box = " E2e Testing"
    analysis_page.analysis_text_box = " E2e testing"
    selenium.find_element_by_id("save-and-continue-btn").click()
    # Fill Risks page
    from pages.experiment_risks_and_testing import RiskAndTestingPage

    risks_page = RiskAndTestingPage(selenium, base_url).wait_for_page_to_load()
    for risk in risks_page.risks:
        risk.select_no()
    risks_page.qa_status_box = "Green"
    detail_page = risks_page.save_btn()
    detail_page.begin_signoffs_button.click()
    for checkbox in detail_page.required_checklist_section:
        try:
            checkbox.checkbox.click()
        except Exception:
            continue
    detail_page.save_sign_offs_button.click()
    detail_page.ready_to_ship_button.click()


@pytest.mark.nondestructive
def test_single_pref_e2e(base_url, selenium, fill_timeline):
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
        ):  # We want to check each branch so we need to do the check for as many branches exist
            if (
                item["slug"]
                == test_json["multi-pref-experiment"]["branches"][num]["branch_name"]
            ):  # Start by checking the name
                assert (
                    test_json["multi-pref-experiment"]["branches"][num][
                        "firefox_pref_name"
                    ]
                    in f"{[key for key in item['preferences']]}"
                )
                assert (
                    test_json["multi-pref-experiment"]["branches"][num][
                        "firefox_pref_type"
                    ]
                    in f"{[value['preferenceType'] for value in item['preferences'].values()]}"
                )
                assert (
                    test_json["multi-pref-experiment"]["branches"][num][
                        "firefox_pref_branch"
                    ]
                    in f"{[value['preferenceBranchType'] for value in item['preferences'].values()]}"
                )
                assert (
                    test_json["multi-pref-experiment"]["branches"][num]["branch_value"]
                    in f"{[value['preferenceValue'] for value in item['preferences'].values()]}".lower()
                )
