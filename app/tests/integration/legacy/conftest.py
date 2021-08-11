import datetime
from urllib.parse import urlparse

import pytest
import requests
from dateutil.parser import parse
from models.base_dataclass import (
    BaseBranchDataClass,
    BaseDataClass,
    BasePreferencesDataClass,
)
from pages.experiment_design import DesignPage
from pages.experiment_detail import DetailPage
from pages.experiment_objective_and_analysis import ObjectiveAndAnalysisPage
from pages.experiment_timeline_and_population import TimelineAndPopulationPage
from pages.home import Home
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


@pytest.fixture
def ds_issue_host():
    return "https://mozilla-hub.atlassian.net/browse/"


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


@pytest.fixture(name="experiment_type", scope="module")
def fixture_experiment_type():
    return "multi-preference-experiment"


@pytest.fixture(name="experiment_name", scope="module")
def fixture_experiment_name():
    return "Pref-Flip Experiment"


@pytest.fixture(name="default_data", scope="module")
def fixture_default_data(experiment_name, experiment_type):
    """Default data needed to create an experiment."""
    branches = []
    preferences = [
        BasePreferencesDataClass(
            preference_branch_name="e2e-testing",
            preference_branch_type="default",
            preference_type="boolean",
            preference_value="true",
        ),
        BasePreferencesDataClass(
            preference_branch_name="e2e-testing",
            preference_branch_type="default",
            preference_type="boolean",
            preference_value="false",
        ),
    ]
    for count, item in enumerate(preferences):
        branches.append(
            BaseBranchDataClass(
                branch_name=f"e2e-default-branch-{count}", preferences=item
            )
        )

    return BaseDataClass(
        type_name=experiment_name,
        action_name=experiment_type,
        experiment_type="channel",
        channels="Nightly",
        min_version=98,
        max_version=99,
        user_facing_name="e2e testing name",
        user_facing_description="e2e testing description",
        branches=sorted(branches, key=lambda x: x.branch_name),
    )


@pytest.fixture
def fill_overview(selenium, base_url, ds_issue_host, default_data):
    """Fills overview page."""
    selenium.get(base_url)
    home = Home(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_experiment()
    experiment.experiment_type = default_data.type_name
    experiment.public_name = default_data.user_facing_name
    experiment.public_description = default_data.user_facing_description
    experiment.internal_description = "Testing in here"
    experiment.ds_issue_url = f"{ds_issue_host}DS-12345"
    experiment.save_btn()
    # Add url to object
    url = urlparse(selenium.current_url)
    experiment.url = url.path
    return experiment


@pytest.fixture
def fill_timeline_page(
    selenium, base_url, request, default_data, experiment_type, fill_overview
):
    """Fills timeline page."""
    timeline = TimelineAndPopulationPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    timeline.wait_for_page_to_load()
    date = f"{datetime.datetime.now()}"
    new_date = parse(date)
    today = f"{new_date.date()}"
    timeline.proposed_start_date = today
    timeline.proposed_experiment_duration = "25"
    timeline.population_percentage = "100.0"
    timeline.firefox_channel = default_data.channels
    timeline.firefox_min_version = f"{default_data.min_version}.0"
    timeline.firefox_max_version = f"{default_data.max_version}.0"
    timeline.save_btn()
    return timeline


@pytest.fixture
def fill_timeline_page_pref_rollout(
    selenium, base_url, request, default_data, experiment_type, fill_overview
):
    """Fills timeline page according to pref rollout requirements."""
    timeline = TimelineAndPopulationPage(
        selenium, base_url, experiment_url=f"{fill_overview.url}"
    ).open()
    timeline.wait_for_page_to_load()
    date = f"{datetime.datetime.now()}"
    new_date = parse(date)
    today = f"{new_date.date()}"
    timeline.proposed_start_date = today
    timeline.proposed_experiment_duration = "25"
    timeline.rollout_playbook = "Low Risk Schedule"
    timeline.firefox_channel = default_data.channels
    timeline.firefox_min_version = f"{default_data.min_version}.0"
    timeline.firefox_max_version = f"{default_data.max_version}.0"
    timeline.save_btn()
    return timeline


@pytest.fixture
def fill_design_page(selenium, base_url, request, fill_overview):
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
def fill_design_page_pref_rollout(
    selenium, base_url, request, default_data, experiment_type, fill_overview
):
    """Fills design page according to pref rollout requirements."""
    design = DesignPage(selenium, base_url, experiment_url=f"{fill_overview.url}").open()
    design = design.wait_for_page_to_load()
    design.design_details = "THE DESIGN IS FANCY"
    prefs = design.rollout_prefs
    pref_data = default_data.branches[0].preferences
    prefs.pref_branch = pref_data.preference_branch_type
    prefs.pref_type = pref_data.preference_type
    prefs.pref_name = pref_data.preference_branch_name
    prefs.pref_value = pref_data.preference_value
    design.save_btn()
    return design


@pytest.fixture
def fill_design_page_addon_rollout(
    selenium, base_url, request, default_data, experiment_type, fill_overview
):
    """Fills design page according to addon rollout requirements."""
    design = DesignPage(selenium, base_url, experiment_url=f"{fill_overview.url}").open()
    design = design.wait_for_page_to_load()
    design.design_details = "THE DESIGN IS FANCY"
    design.enable_addon_rollout()
    prefs = design.rollout_prefs
    prefs.addon_url = default_data.branches[0].addon_url
    design.save_btn()
    return design


@pytest.fixture
def fill_design_page_generic_experiment(
    selenium, base_url, request, default_data, experiment_type, fill_overview
):
    """Fills design page according to single pref requirements."""
    design = DesignPage(selenium, base_url, experiment_url=f"{fill_overview.url}").open()
    current_branches = design.current_branches
    design.design_details = "THE DESIGN IS FANCY"
    control_branch = current_branches[0]
    control_branch.branch_name = default_data.branches[0].branch_name
    control_branch.branch_description = "THIS IS A TEST"
    current_branches[1].branch_name = default_data.branches[1].branch_name
    current_branches[1].branch_description = "THIS IS A TEST"
    design.save_btn()
    return design


@pytest.fixture
def fill_design_page_multi_prefs(
    selenium, base_url, request, default_data, experiment_type, fill_overview
):
    """Fills design page according to multi pref requirements."""
    design = DesignPage(selenium, base_url, experiment_url=f"{fill_overview.url}").open()
    design = design.wait_for_page_to_load()
    design.enable_multipref()
    branches = design.current_branches
    for count, branch in enumerate(default_data.branches):
        branches[count].branch_name = branch.branch_name
        branches[count].branch_description = branch.branch_description
        branches[count].add_pref_button.click()
        prefs = branches[count].prefs(count)
        for pref_num, item in enumerate(branch.preferences):  # Fill in multi prefs
            prefs[pref_num].pref_branch = item.preference_branch_type
            prefs[pref_num].pref_type = item.preference_type
            prefs[pref_num].pref_name = item.preference_branch_name
            prefs[pref_num].pref_value = item.preference_value
    design.save_btn()
    return design


@pytest.fixture
def fill_design_page_single_pref(
    selenium, base_url, request, default_data, experiment_type, fill_overview
):
    """Fills design page according to single pref requirements."""
    design = DesignPage(selenium, base_url, experiment_url=f"{fill_overview.url}").open()
    design = design.wait_for_page_to_load()
    design.input_firefox_pref_name(
        default_data.branches[0].preferences.preference_branch_name
    )
    design.select_firefox_pref_type(default_data.branches[0].preferences.preference_type)
    design.select_firefox_pref_branch(
        default_data.branches[0].preferences.preference_branch_type
    )
    current_branchs = design.current_branches
    control_branch = current_branchs[0]
    control_branch.branch_name = default_data.branches[0].branch_name
    control_branch.branch_description = "THIS IS A TEST"
    control_branch.branch_value = default_data.branches[0].preferences.preference_value
    current_branchs[1].branch_name = default_data.branches[1].branch_name
    current_branchs[1].branch_description = "THIS IS A TEST"
    current_branchs[1].branch_value = default_data.branches[
        1
    ].preferences.preference_value
    design.save_btn()
    return design


@pytest.fixture
def fill_design_page_branched_single_addon(
    selenium, base_url, request, default_data, experiment_type, fill_overview
):
    """Fills design page according to branched single addon requirements."""
    design = DesignPage(selenium, base_url, experiment_url=f"{fill_overview.url}").open()
    design = design.wait_for_page_to_load()
    design.signed_addon_url = default_data.addon_url
    current_branchs = design.current_branches
    control_branch = current_branchs[0]
    control_branch.branch_name = default_data.branches[0].branch_name
    control_branch.branch_description = "THIS IS A TEST"
    control_branch.branch_description = default_data.branches[0].branch_description
    current_branchs[1].branch_name = default_data.branches[1].branch_name
    current_branchs[1].branch_description = "THIS IS A TEST"
    current_branchs[1].branch_description = default_data.branches[1].branch_description
    design.save_btn()
    return design


@pytest.fixture
def fill_design_page_branched_multi_addon(
    selenium, base_url, request, default_data, experiment_type, fill_overview
):
    """Fills design page according to branched multi addon requirements."""
    design = DesignPage(selenium, base_url, experiment_url=f"{fill_overview.url}").open()
    design = design.wait_for_page_to_load()
    design.enable_multi_addon()
    current_branchs = design.current_branches
    control_branch = current_branchs[0]
    control_branch.branch_name = default_data.branches[0].branch_name
    control_branch.branch_description = "THIS IS A TEST"
    control_branch.branch_description = default_data.branches[0].branch_description
    control_branch.signed_addon_url = default_data.branches[0].addon_url
    current_branchs[1].branch_name = default_data.branches[1].branch_name
    current_branchs[1].branch_description = "THIS IS A TEST"
    current_branchs[1].branch_description = default_data.branches[1].branch_description
    current_branchs[1].signed_addon_url = default_data.branches[1].addon_url
    design.save_btn()
    return design


@pytest.fixture
def fill_analysis_page(selenium, base_url, request, fill_overview):
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
def fill_risks_page(selenium, base_url, request, fill_overview):
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
    """ "Fills signoffs and clicks 'Confirm ready to ship' button."""
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
