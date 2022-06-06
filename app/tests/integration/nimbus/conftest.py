import uuid
from urllib.parse import urljoin, urlparse

import pytest
import requests
from nimbus.kinto.client import (
    KINTO_COLLECTION_DESKTOP,
    KINTO_COLLECTION_MOBILE,
    KintoClient,
)
from nimbus.models.base_dataclass import (
    BaseExperimentApplications,
    BaseExperimentAudienceChannels,
    BaseExperimentAudienceDataClass,
    BaseExperimentBranchDataClass,
    BaseExperimentDataClass,
    BaseExperimentMetricsDataClass,
)
from nimbus.pages.experimenter.home import HomePage
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

APPLICATION_FEATURES = {
    BaseExperimentApplications.DESKTOP: "No Feature Firefox Desktop",
    BaseExperimentApplications.FENIX: "No Feature Fenix",
    BaseExperimentApplications.IOS: "No Feature iOS",
    BaseExperimentApplications.FOCUS_ANDROID: "No Feature Focus for Android",
    BaseExperimentApplications.FOCUS_IOS: "No Feature Focus for iOS",
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
    BaseExperimentApplications.FOCUS_ANDROID: (
        "#/buckets/main-workspace/collections/nimbus-mobile-experiments/simple-review"
    ),
    BaseExperimentApplications.FOCUS_IOS: (
        "#/buckets/main-workspace/collections/nimbus-mobile-experiments/simple-review"
    ),
}

APPLICATION_KINTO_COLLECTION = {
    "DESKTOP": KINTO_COLLECTION_DESKTOP,
    "FENIX": KINTO_COLLECTION_MOBILE,
    "IOS": KINTO_COLLECTION_MOBILE,
    "FOCUS_ANDROID": KINTO_COLLECTION_MOBILE,
    "FOCUS_IOS": KINTO_COLLECTION_MOBILE,
}


@pytest.fixture
def slugify():
    def _slugify(input):
        return input.lower().replace(" ", "-").replace("[", "").replace("]", "")

    return _slugify


@pytest.fixture
def json_url(slugify):
    def _json_url(base_url, title):
        base_url = urlparse(base_url)
        return f"https://{base_url.netloc}/api/v6/experiments/{slugify(title)}"

    return _json_url


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
def kinto_client(default_data):
    return KintoClient(APPLICATION_KINTO_COLLECTION[default_data.application.value])


@pytest.fixture
def archived_tab_url(base_url):
    return f"{base_url}?tab=archived"


@pytest.fixture
def drafts_tab_url(base_url):
    return f"{base_url}?tab=drafts"


@pytest.fixture
def experiment_url(base_url, default_data, slugify):
    return urljoin(base_url, slugify(default_data.public_name))


@pytest.fixture
def experiment_name(request):
    return f"{request.node.name[:76]}-{str(uuid.uuid4())[:4]}"


@pytest.fixture(
    # Use all applications as available parameters in parallel_pytest_args.txt
    params=list(BaseExperimentApplications),
    ids=[application.name for application in BaseExperimentApplications],
)
def default_data(request, experiment_name):
    application = request.param
    feature_config = APPLICATION_FEATURES[application]

    return BaseExperimentDataClass(
        public_name=experiment_name,
        hypothesis="smart stuff here",
        application=application,
        public_description="description stuff",
        feature_config=feature_config,
        branches=[
            BaseExperimentBranchDataClass(
                name="control",
                description="control description",
            ),
            BaseExperimentBranchDataClass(
                name="treatment",
                description="treatment description",
            ),
        ],
        metrics=BaseExperimentMetricsDataClass(
            primary_outcomes=[], secondary_outcomes=[]
        ),
        audience=BaseExperimentAudienceDataClass(
            channel=BaseExperimentAudienceChannels.RELEASE,
            min_version=80,
            targeting="",
            percentage=50.0,
            expected_clients=50,
            locale=None,
            countries=None,
        ),
    )


@pytest.fixture
def create_experiment(base_url, default_data):
    def _create_experiment(selenium):
        home = HomePage(selenium, base_url).open()
        experiment = home.create_new_button()
        experiment.public_name = default_data.public_name
        experiment.hypothesis = default_data.hypothesis
        experiment.application = default_data.application.value

        # Fill Overview Page
        overview = experiment.save_and_continue()
        overview.public_description = default_data.public_description
        overview.select_risk_brand_false()
        overview.select_risk_revenue_false()
        overview.select_risk_partner_false()

        # Fill Branches page
        branches = overview.save_and_continue()
        branches.feature_config = default_data.feature_config
        branches.reference_branch_description = default_data.branches[0].description
        branches.treatment_branch_description = default_data.branches[0].description
        branches.treatment_branch_enabled.click()
        branches.treatment_branch_value = '{"value": true}'

        # Fill Metrics page
        metrics = branches.save_and_continue()

        # Fill Audience page
        audience = metrics.save_and_continue()
        audience.channel = default_data.audience.channel.value
        audience.min_version = default_data.audience.min_version
        audience.targeting = default_data.audience.targeting
        audience.percentage = default_data.audience.percentage
        audience.expected_clients = default_data.audience.expected_clients
        return audience.save_and_continue()

    return _create_experiment


@pytest.fixture
def create_mobile_experiment():
    def _create_mobile_experiment(name, app, locales, targeting):
        query = {
            "operationName": "createExperiment",
            "variables": {
                "input": {
                    "name": name,
                    "hypothesis": "Test hypothesis",
                    "application": app.upper(),
                    "locales": locales,
                    "changelogMessage": "test changelog message",
                    "targetingConfigSlug": targeting,
                }
            },
            "query": "mutation createExperiment($input: ExperimentInput!) \
                {\n  createExperiment(input: $input) \
                {\n    message\n    nimbusExperiment \
                {\n      slug\n      __typename\n    }\n    __typename\n  }\
                \n}",
        }
        requests.post("https://nginx/api/v5/graphql", json=query, verify=False)

    return _create_mobile_experiment
