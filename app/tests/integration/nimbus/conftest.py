import uuid
from urllib.parse import urljoin

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
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

APPLICATION_FEATURES = {
    BaseExperimentApplications.DESKTOP: "No Feature Firefox Desktop",
    BaseExperimentApplications.FENIX: "No Feature Fenix",
    BaseExperimentApplications.IOS: "No Feature iOS",
    BaseExperimentApplications.KLAR: "No Feature Klar for Android",
    BaseExperimentApplications.FOCUS: "No Feature Focus for Android",
}

APPLICATION_KINTO_REVIEW_PATH = {
    BaseExperimentApplications.DESKTOP: (
        "#/buckets/main-workspace/collections/nimbus-desktop-experiments/simple-review"
    ),
    BaseExperimentApplications.FENIX: (
        "#/buckets/main-workspace/collections/nimbus-mobile-experiments/simple-review"
    ),
    BaseExperimentApplications.IOS: (
        "#/buckets/main-workspace/collections/nimbus-mobile-experiments/simple-review"
    ),
    BaseExperimentApplications.KLAR: (
        "#/buckets/main-workspace/collections/nimbus-mobile-experiments/simple-review"
    ),
    BaseExperimentApplications.FOCUS: (
        "#/buckets/main-workspace/collections/nimbus-mobile-experiments/simple-review"
    ),
}


def slugify(input):
    return input.lower().replace(" ", "-").replace("[", "").replace("]", "")


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
def kinto_url():
    return "http://kinto:8888/v1/admin/"


@pytest.fixture
def kinto_review_url(kinto_url, default_data):
    return urljoin(kinto_url, APPLICATION_KINTO_REVIEW_PATH[default_data.application])


@pytest.fixture
def experiment_url(base_url, default_data):
    return urljoin(base_url, slugify(default_data.public_name))


@pytest.fixture(
    # Use all applications as available parameters in parallel_pytest_args.txt
    params=list(BaseExperimentApplications),
    ids=[application.name for application in BaseExperimentApplications],
)
def default_data(request):
    application = request.param
    feature = APPLICATION_FEATURES[application]

    return BaseExperimentDataClass(
        public_name=f"{request.node.name}-{str(uuid.uuid4())[:4]}",
        hypothesis="smart stuff here",
        application=application,
        public_description="description stuff",
        branches=[
            BaseExperimentBranchDataClass(
                name="name 1",
                description="a nice experiment",
                feature_config=feature,
            )
        ],
        metrics=BaseExperimentMetricsDataClass(
            primary_outcomes=[], secondary_outcomes=[]
        ),
        audience=BaseExperimentAudienceDataClass(
            channel=BaseExperimentAudienceChannels.RELEASE,
            min_version=80,
            targeting=BaseExperimentAudienceTargetingOptions.NO_TARGETING,
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
