import os

import pytest
import requests
from nimbus.models.base_dataclass import (
    BaseExperimentApplications,
    BaseExperimentAudienceChannels,
    BaseExperimentAudienceDataClass,
    BaseExperimentAudienceTargetingOptions,
    BaseExperimentBranchDataClass,
    BaseExperimentDataClass,
    BaseExperimentMetricsDataClass,
)
from nimbus.remote_settings.pages.dashboard import Dashboard
from nimbus.remote_settings.pages.login import Login
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from selenium.common.exceptions import NoSuchElementException


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
def default_data():
    return BaseExperimentDataClass(
        public_name="test_experiment",
        hypothesis="smart stuff here",
        application=BaseExperimentApplications.DESKTOP,
        public_description="description stuff",
        branches=[
            BaseExperimentBranchDataClass(
                name="name 1",
                description="a nice experiment",
                feature_config="No Feature Firefox Desktop",
            )
        ],
        metrics=BaseExperimentMetricsDataClass(
            primary_outcomes=[], secondary_outcomes=[]
        ),
        audience=BaseExperimentAudienceDataClass(
            channel=BaseExperimentAudienceChannels.NIGHTLY,
            min_version=80,
            targeting=BaseExperimentAudienceTargetingOptions.TARGETING_MAC_ONLY,
            percentage=50.0,
            expected_clients=50,
        ),
    )


@pytest.fixture
def create_experiment():
    def _create_experiment(selenium, home_page, data):
        experiment = home_page.create_new_button()
        experiment.public_name = data.public_name
        experiment.hypothesis = data.hypothesis
        experiment.application = data.application.value

        # Fill Overview Page
        overview = experiment.save_and_continue()
        overview.public_description = data.public_description
        overview.select_risk_brand_false()
        overview.select_risk_revenue_false()
        overview.select_risk_partner_false()

        # Fill Branches page
        branches = overview.save_and_continue()
        branches.remove_branch()
        branches.reference_branch_name = data.branches[0].name
        branches.reference_branch_description = data.branches[0].description
        branches.feature_config = data.branches[0].feature_config

        # Fill Metrics page
        metrics = branches.save_and_continue()

        # Fill Audience page
        audience = metrics.save_and_continue()
        audience.channel = data.audience.channel.value
        audience.min_version = data.audience.min_version
        audience.targeting = data.audience.targeting.value
        audience.percentage = data.audience.percentage
        audience.expected_clients = data.audience.expected_clients
        audience.save_btn()
        review = audience.save_and_continue()

        # Review
        selenium.find_element_by_css_selector("#PageSummary")
        return review

    return _create_experiment


@pytest.fixture
def perform_kinto_action():
    def _perform_kinto_action(selenium, base_url, action):
        selenium.get("http://kinto:8888/v1/admin")
        try:
            kinto_login = Login(selenium, base_url).wait_for_page_to_load()
            kinto_login.kinto_auth.click()
            kinto_dashbard = kinto_login.login()
        except NoSuchElementException:
            kinto_dashbard = Dashboard(selenium, base_url).wait_for_page_to_load()
        bucket = kinto_dashbard.buckets[-1]
        for item in bucket.bucket_category:
            if "nimbus-desktop-experiments" in item.text:
                item.click()
                break
        record = kinto_dashbard.record
        record.action(action)
        if action == "reject":
            kinto_dashbard = Dashboard(selenium, base_url)
            modal = kinto_dashbard.reject_modal
            modal.decline_changes()

    return _perform_kinto_action
