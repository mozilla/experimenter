import datetime
from dateutil.parser import parse
import os
from urllib.parse import urlparse

import pytest
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from pages.home import Home
from pages.experiment_timeline_and_population import TimelineAndPopulationPage
from pages.experiment_design import DesignPage
from pages.experiment_detail import DetailPage
from pages.experiment_objective_and_analysis import ObjectiveAndAnalysisPage


@pytest.fixture
def ds_issue_host():
    return os.environ["DS_ISSUE_HOST"]


@pytest.fixture
def capabilities(capabilities):
    capabilities["acceptInsecureCerts"] = True
    return capabilities


@pytest.fixture
def sensitive_url():
    pass


@pytest.fixture
def firefox_options(firefox_options):
    """Set Firefox Options."""
    firefox_options.log.level = "trace"
    return firefox_options


@pytest.fixture(scope="session", autouse=True)
def _verify_url(request, base_url):
    """Verifies the base URL"""
    verify = request.config.option.verify_base_url
    if base_url and verify:
        session = requests.Session()
        retries = Retry(backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        session.mount(base_url, HTTPAdapter(max_retries=retries))
        session.get(base_url, verify=False)


@pytest.fixture
def fill_overview(selenium, base_url, ds_issue_host, request, variables):
    """Fills overview page."""
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    experiment_type = getattr(request.module, "experiment_type", None)
    experiment.experiment_type = getattr(
        request.module, "experiment_type_name", "Pref-Flip Experiment"
    )
    if request.node.get_closest_marker("use_variables"):
        experiment.name = f"{variables[experiment_type]['name']}"
        experiment.short_description = "Testing in here"
        experiment.public_name = f"{variables[experiment_type]['userFacingName']}"
        experiment.public_description = (
            f"{variables[experiment_type]['userFacingDescription']}"
        )
    else:
        experiment.name = "This is a test"
        experiment.short_description = "Testing in here"
        experiment.public_name = "Public Name"
        experiment.public_description = "Public Description"
        experiment.ds_issue_url = f"{ds_issue_host}DS-12345"
    experiment.ds_issue_url = f"{ds_issue_host}DS-12345"
    experiment.save_btn()
    # Add url to object
    url = urlparse(selenium.current_url)
    experiment.url = url.path
    return experiment


@pytest.fixture
def fill_timeline_page(selenium, base_url, request, variables, fill_overview):
    """Fills timeline page."""
    experiment_type = getattr(request.module, "experiment_type", None)
    timeline = TimelineAndPopulationPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    timeline.wait_for_page_to_load()
    date = f"{datetime.datetime.now()}"
    new_date = parse(date)
    today = f"{new_date.date()}"
    timeline.proposed_start_date = today
    timeline.proposed_experiment_duration = "25"
    timeline.population_precentage = "100.0"
    if request.node.get_closest_marker("use_variables"):
        timeline.firefox_channel = f"{variables[experiment_type]['channels']}"
        timeline.firefox_min_version = f"{variables[experiment_type]['min_version']}"
        timeline.firefox_max_version = f"{variables[experiment_type]['max_version']}"
    else:
        timeline.firefox_channel = "nightly"
        timeline.firefox_min_version = "75"
        timeline.firefox_max_version = "100"
    timeline.save_btn()
    return timeline


@pytest.fixture
def fill_design_page(selenium, base_url, request, variables, fill_overview):
    """Fills design page according to generic requirements."""
    design = DesignPage(selenium, base_url, experiment_url=f"{fill_overview.url}").open()
    design = design.wait_for_page_to_load()
    design.input_firefox_pref_name("default_fixture")
    design.select_firefox_pref_type("boolean")
    design.select_firefox_pref_branch("default")
    current_branchs = design.current_branches
    control_branch = current_branchs[0]
    control_branch.branch_name = "Fixture Branch"
    control_branch.branch_description = "THIS IS A TEST"
    control_branch.branch_value = "true"
    current_branchs[1].branch_name = "Fixture Branch 2"
    current_branchs[1].branch_description = "THIS IS A TEST"
    current_branchs[1].branch_value = "false"
    design.save_btn()
    return design


@pytest.fixture
def fill_design_page_multi_prefs(selenium, base_url, request, variables, fill_overview):
    """Fills design page according to multi pref requirements."""
    experiment_type = getattr(request.module, "experiment_type", None)
    design = DesignPage(selenium, base_url, experiment_url=f"{fill_overview.url}").open()
    design = design.wait_for_page_to_load()
    design.enable_multipref()
    branches = design.current_branches
    for count, branch in enumerate(variables[experiment_type]["branches"]):
        branches[count].branch_name = f"{branch['branch_name']}"
        branches[count].branch_description = f"{branch['branch_description']}"
        branches[count].add_pref_button.click()
        prefs = branches[count].prefs(count)
        for pref_num in range(0, len(branch["preferences"])):  # Fill in multi prefs
            prefs[
                pref_num
            ].pref_branch = f"{branch['preferences'][pref_num]['firefox_pref_branch']}"
            prefs[
                pref_num
            ].pref_type = f"{branch['preferences'][pref_num]['firefox_pref_type']}"
            prefs[
                pref_num
            ].pref_name = f"{branch['preferences'][pref_num]['firefox_pref_name']}"
            prefs[
                pref_num
            ].pref_value = f"{branch['preferences'][pref_num]['firefox_pref_value']}"
    design.save_btn()
    return design


@pytest.fixture
def fill_design_page_single_pref(selenium, base_url, request, variables, fill_overview):
    """Fills design page according to single pref requirements."""
    experiment_type = getattr(request.module, "experiment_type", None)
    design = DesignPage(selenium, base_url, experiment_url=f"{fill_overview.url}").open()
    design = design.wait_for_page_to_load()
    design.input_firefox_pref_name(
        f"{variables[experiment_type]['branches'][0]['firefox_pref_name']}"
    )
    design.select_firefox_pref_type(
        f"{variables[experiment_type]['branches'][0]['firefox_pref_type']}"
    )
    design.select_firefox_pref_branch(
        f"{variables[experiment_type]['branches'][0]['firefox_pref_branch']}"
    )
    current_branchs = design.current_branches
    control_branch = current_branchs[0]
    control_branch.branch_name = (
        f"{variables[experiment_type]['branches'][0]['branch_name']}"
    )
    control_branch.branch_description = "THIS IS A TEST"
    control_branch.branch_value = (
        f"{variables[experiment_type]['branches'][0]['branch_value']}"
    )
    current_branchs[
        1
    ].branch_name = f"{variables[experiment_type]['branches'][1]['branch_name']}"
    current_branchs[1].branch_description = "THIS IS A TEST"
    current_branchs[
        1
    ].branch_value = f"{variables[experiment_type]['branches'][1]['branch_value']}"
    design.save_btn()
    return design


@pytest.fixture
def fill_design_page_branched_single_addon(
    selenium, base_url, request, variables, fill_overview
):
    """Fills design page according to branched single addon requirements."""
    experiment_type = getattr(request.module, "experiment_type", None)
    design = DesignPage(selenium, base_url, experiment_url=f"{fill_overview.url}").open()
    design = design.wait_for_page_to_load()
    design.signed_addon_url = f"{variables[experiment_type]['addon_url']}"
    current_branchs = design.current_branches
    control_branch = current_branchs[0]
    control_branch.branch_name = (
        f"{variables[experiment_type]['branches'][0]['branch_name']}"
    )
    control_branch.branch_description = "THIS IS A TEST"
    control_branch.branch_description = (
        f"{variables[experiment_type]['branches'][0]['branch_description']}"
    )
    current_branchs[
        1
    ].branch_name = f"{variables[experiment_type]['branches'][1]['branch_name']}"
    current_branchs[1].branch_description = "THIS IS A TEST"
    current_branchs[
        1
    ].branch_description = (
        f"{variables[experiment_type]['branches'][1]['branch_description']}"
    )
    design.save_btn()
    return design


@pytest.fixture
def fill_design_page_branched_multi_addon(
    selenium, base_url, request, variables, fill_overview
):
    """Fills design page according to branched multi addon requirements."""
    experiment_type = getattr(request.module, "experiment_type", None)
    design = DesignPage(selenium, base_url, experiment_url=f"{fill_overview.url}").open()
    design = design.wait_for_page_to_load()
    design.enable_multi_addon()
    current_branchs = design.current_branches
    control_branch = current_branchs[0]
    control_branch.branch_name = (
        f"{variables[experiment_type]['branches'][0]['branch_name']}"
    )
    control_branch.branch_description = "THIS IS A TEST"
    control_branch.branch_description = (
        f"{variables[experiment_type]['branches'][0]['branch_description']}"
    )
    control_branch.signed_addon_url = (
        f"{variables[experiment_type]['branches'][0]['addon_url']}"
    )
    current_branchs[
        1
    ].branch_name = f"{variables[experiment_type]['branches'][1]['branch_name']}"
    current_branchs[1].branch_description = "THIS IS A TEST"
    current_branchs[
        1
    ].branch_description = (
        f"{variables[experiment_type]['branches'][1]['branch_description']}"
    )
    current_branchs[
        1
    ].signed_addon_url = f"{variables[experiment_type]['branches'][0]['addon_url']}"
    design.save_btn()
    return design


@pytest.fixture
def fill_analysis_page(selenium, base_url, request, variables, fill_overview):
    """Fills analysis page."""
    analysis_page = ObjectiveAndAnalysisPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    analysis_page.wait_for_page_to_load()
    analysis_page.objectives_text_box = " E2e Testing"
    analysis_page.analysis_text_box = " E2e testing"
    analysis_page.save_btn()
    return analysis_page


@pytest.fixture
def fill_risks_page(selenium, base_url, request, variables, fill_overview):
    """Fills risks page."""
    from pages.experiment_risks_and_testing import RiskAndTestingPage

    risks_page = RiskAndTestingPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    risks_page.wait_for_page_to_load()
    for risk in risks_page.risks:
        risk.select_no()
    risks_page.qa_status_box = "Green"
    risks_page.save_btn()
    return risks_page


@pytest.fixture
def signoff_and_ship(selenium, base_url, fill_overview):
    """"Fills signoffs and clicks 'Confirm ready to ship' button."""
    detail_page = DetailPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).wait_for_page_to_load()
    detail_page.begin_signoffs_button.click()
    for checkbox in detail_page.required_checklist_section:
        try:
            checkbox.checkbox.click()
        except Exception:
            continue
    detail_page.save_sign_offs_button.click()
    detail_page.ready_to_ship_button.click()


@pytest.fixture
def fill_experiment(
    base_url,
    selenium,
    variables,
    ds_issue_host,
    fill_overview,
    fill_timeline_page,
    fill_design_page,
    fill_analysis_page,
    fill_risks_page,
):
    # fills experiment and gets it ready to ship
    print(fill_overview.url)
    detail_page = DetailPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).wait_for_page_to_load()
    detail_page.begin_signoffs_button.click()
    for checkbox in detail_page.required_checklist_section:
        try:
            checkbox.checkbox.click()
        except Exception:
            continue
    detail_page.save_sign_offs_button.click()
    detail_page.ready_to_ship_button.click()
