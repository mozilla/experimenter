import os
import time
import uuid
from urllib.parse import urljoin

import pytest
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from nimbus.kinto.client import (
    KINTO_COLLECTION_DESKTOP,
    KINTO_COLLECTION_MOBILE,
    KINTO_COLLECTION_WEB,
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
from nimbus.pages.demo_app.frontend import DemoAppPage
from nimbus.pages.experimenter.home import HomePage
from nimbus.utils import helpers

APPLICATION_FEATURE_IDS = {
    BaseExperimentApplications.FIREFOX_DESKTOP.value: helpers.get_feature_id_as_string(
        "no-feature-firefox-desktop", BaseExperimentApplications.FIREFOX_DESKTOP.value
    ),
    BaseExperimentApplications.FIREFOX_FENIX.value: helpers.get_feature_id_as_string(
        "no-feature-fenix", BaseExperimentApplications.FIREFOX_FENIX.value
    ),
    BaseExperimentApplications.FIREFOX_IOS.value: helpers.get_feature_id_as_string(
        "no-feature-ios", BaseExperimentApplications.FIREFOX_IOS.value
    ),
    BaseExperimentApplications.FOCUS_ANDROID.value: helpers.get_feature_id_as_string(
        "no-feature-focus-android", BaseExperimentApplications.FOCUS_ANDROID.value
    ),
    BaseExperimentApplications.FOCUS_IOS.value: helpers.get_feature_id_as_string(
        "no-feature-focus-ios", BaseExperimentApplications.FOCUS_IOS.value
    ),
    BaseExperimentApplications.DEMO_APP.value: helpers.get_feature_id_as_string(
        "example-feature", BaseExperimentApplications.DEMO_APP.value
    ),
}


APPLICATION_KINTO_REVIEW_PATH = {
    BaseExperimentApplications.FIREFOX_DESKTOP.value: (
        "#/buckets/main-workspace/collections/nimbus-desktop-experiments/simple-review"
    ),
    BaseExperimentApplications.FIREFOX_FENIX.value: (
        "#/buckets/main-workspace/collections/nimbus-mobile-experiments/simple-review"
    ),
    BaseExperimentApplications.FIREFOX_IOS.value: (
        "#/buckets/main-workspace/collections/nimbus-mobile-experiments/simple-review"
    ),
    BaseExperimentApplications.FOCUS_ANDROID.value: (
        "#/buckets/main-workspace/collections/nimbus-mobile-experiments/simple-review"
    ),
    BaseExperimentApplications.FOCUS_IOS.value: (
        "#/buckets/main-workspace/collections/nimbus-mobile-experiments/simple-review"
    ),
    BaseExperimentApplications.DEMO_APP.value: (
        "#/buckets/main-workspace/collections/nimbus-web-experiments/simple-review"
    ),
}

APPLICATION_KINTO_COLLECTION = {
    BaseExperimentApplications.FIREFOX_DESKTOP.value: KINTO_COLLECTION_DESKTOP,
    BaseExperimentApplications.FIREFOX_FENIX.value: KINTO_COLLECTION_MOBILE,
    BaseExperimentApplications.FIREFOX_IOS.value: KINTO_COLLECTION_MOBILE,
    BaseExperimentApplications.FOCUS_ANDROID.value: KINTO_COLLECTION_MOBILE,
    BaseExperimentApplications.FOCUS_IOS.value: KINTO_COLLECTION_MOBILE,
    BaseExperimentApplications.DEMO_APP.value: KINTO_COLLECTION_WEB,
}


def slugify(name):
    return name.lower().replace(" ", "-").replace("[", "").replace("]", "")


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


@pytest.fixture
def selenium(selenium, experiment_slug, kinto_client):
    yield selenium

    if os.getenv("CIRCLECI") is None:
        try:
            helpers.end_experiment(experiment_slug)
            kinto_client.approve()
        except Exception:
            pass


@pytest.fixture(
    # Use all applications as available parameters in circle config
    params=list(BaseExperimentApplications),
    ids=[application.name for application in BaseExperimentApplications],
    autouse=True,
)
def application(request):
    return request.param.value


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
    return KintoClient(APPLICATION_KINTO_COLLECTION[default_data.application])


@pytest.fixture
def archived_tab_url(base_url):
    return f"{base_url}?tab=archived"


@pytest.fixture
def drafts_tab_url(base_url):
    return f"{base_url}?tab=drafts"


@pytest.fixture
def experiment_name(request):
    return f"{request.node.name[:75]}{str(uuid.uuid4())[:4]}"


@pytest.fixture
def experiment_slug(experiment_name):
    return slugify(experiment_name)


@pytest.fixture
def experiment_url(base_url, experiment_slug):
    return urljoin(base_url, experiment_slug)


@pytest.fixture(name="load_experiment_outcomes")
def fixture_load_experiment_outcomes():
    """Fixture to create a list of outcomes based on the current configs."""
    outcomes = {"firefox_desktop": "", "fenix": "", "firefox_ios": ""}
    base_path = (
        "/code/experimenter/experimenter/outcomes/metric-hub-main/jetstream/outcomes"
    )

    for k in list(outcomes):
        outcomes[k] = [
            name.split("_")[0].rsplit(".")[0]
            for name in os.listdir(f"{base_path}/{k}")
            if "example" not in name
        ]
    return outcomes


@pytest.fixture
def default_data(application, experiment_name, load_experiment_outcomes):
    feature_config_id = APPLICATION_FEATURE_IDS[application]

    outcomes = {
        BaseExperimentApplications.FIREFOX_DESKTOP.value: BaseExperimentMetricsDataClass(
            primary_outcomes=[load_experiment_outcomes["firefox_desktop"][0]],
            secondary_outcomes=[load_experiment_outcomes["firefox_desktop"][1]],
        ),
        BaseExperimentApplications.FIREFOX_FENIX.value: BaseExperimentMetricsDataClass(
            primary_outcomes=[load_experiment_outcomes["fenix"][0]],
            secondary_outcomes=[load_experiment_outcomes["fenix"][1]],
        ),
        BaseExperimentApplications.FIREFOX_IOS.value: BaseExperimentMetricsDataClass(
            primary_outcomes=[load_experiment_outcomes["firefox_ios"][0]],
            secondary_outcomes=[load_experiment_outcomes["firefox_ios"][1]],
        ),
    }

    return BaseExperimentDataClass(
        public_name=experiment_name,
        hypothesis="smart stuff here",
        application=application,
        public_description="description stuff",
        feature_config_id=feature_config_id,
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
        metrics=outcomes.get(
            application,
            BaseExperimentMetricsDataClass(
                primary_outcomes=[],
                secondary_outcomes=[],
            ),
        ),
        audience=BaseExperimentAudienceDataClass(
            channel=BaseExperimentAudienceChannels.RELEASE,
            min_version=106,
            targeting="test_targeting",
            percentage="50",
            expected_clients=50,
            locale=None,
            countries=None,
            languages=None,
        ),
        is_rollout=False,
    )


@pytest.fixture
def create_experiment(base_url, default_data):
    def _create_experiment(
        selenium,
        is_rollout=False,
        reference_branch_value="{}",
        treatment_branch_value="{}",
    ):
        home = HomePage(selenium, base_url).open()
        experiment = home.create_new_button()
        experiment.public_name = default_data.public_name
        experiment.hypothesis = default_data.hypothesis
        experiment.application = default_data.application

        # Fill Overview Page
        overview = experiment.save_and_continue()
        overview.select_risk_brand_false()
        overview.select_risk_revenue_false()
        overview.select_risk_partner_false()
        overview.public_description = default_data.public_description
        overview.set_additional_links(value="DESIGN_DOC")
        overview.add_additional_links()
        overview.set_additional_links(value="DS_JIRA", url="https://jira.jira.com")
        overview.add_additional_links()
        overview.set_additional_links(
            value="ENG_TICKET", url="https://www.smarter-engineering.eng"
        )
        overview.projects = [helpers.load_config_data()["projects"][0]["name"]]

        # Fill Branches page
        branches = overview.save_and_continue()
        branches.feature_config = default_data.feature_config_id
        branches.reference_branch_description = default_data.branches[0].description
        branches.reference_branch_value = reference_branch_value

        if is_rollout:
            branches.make_rollout()
        else:
            branches.treatment_branch_description = default_data.branches[1].description
            branches.treatment_branch_value = treatment_branch_value

        # Fill Metrics page
        metrics = branches.save_and_continue()
        if default_data.metrics.primary_outcomes:
            metrics.set_primary_outcomes(values=default_data.metrics.primary_outcomes[0])
            assert metrics.primary_outcomes.text != "", "The primary outcome was not set"
            metrics.set_secondary_outcomes(
                values=default_data.metrics.secondary_outcomes[0]
            )
            assert (
                metrics.secondary_outcomes.text != ""
            ), "The seconday outcome was not set"

        # Fill Audience page
        audience = metrics.save_and_continue()
        audience.channel = default_data.audience.channel.value

        audience.targeting = "no_targeting"
        audience.percentage = "100"
        audience.expected_clients = default_data.audience.expected_clients
        if default_data.application != BaseExperimentApplications.DEMO_APP.value:
            audience.min_version = default_data.audience.min_version
            audience.percentage = default_data.audience.percentage
            audience.targeting = default_data.audience.targeting
            audience.countries = ["Canada"]
            if (
                default_data.application
                != BaseExperimentApplications.FIREFOX_DESKTOP.value
            ):
                audience.languages = ["English"]
            else:
                audience.locales = ["English (US)"]
        return audience.save_and_continue()

    return _create_experiment


@pytest.fixture
def trigger_experiment_loader(selenium):
    def _trigger_experiment_loader():
        with selenium.context(selenium.CONTEXT_CHROME):
            selenium.execute_script(
                """
                    const { RemoteSettings } = ChromeUtils.import(
                        "resource://services-settings/remote-settings.js"
                    );
                    const { RemoteSettingsExperimentLoader } = ChromeUtils.import(
                        "resource://nimbus/lib/RemoteSettingsExperimentLoader.jsm"
                    );

                    RemoteSettings.pollChanges();
                    RemoteSettingsExperimentLoader.updateRecipes();
                """
            )
        time.sleep(5)

    return _trigger_experiment_loader


@pytest.fixture()
def default_data_api(application):
    feature_config_id = APPLICATION_FEATURE_IDS[application]
    return {
        "hypothesis": "Test Hypothesis",
        "application": application,
        "changelogMessage": "test updates",
        "targetingConfigSlug": "no_targeting",
        "publicDescription": "Some sort of Fancy Words",
        "riskRevenue": False,
        "riskPartnerRelated": False,
        "riskBrand": False,
        "featureConfigIds": [int(feature_config_id)],
        "referenceBranch": {
            "description": "reference branch",
            "name": "Branch 1",
            "ratio": 50,
            "featureValues": [
                {
                    "featureConfig": str(feature_config_id),
                    "value": "{}",
                },
            ],
        },
        "treatmentBranches": [],
        "populationPercent": "100",
        "totalEnrolledClients": 55,
        "firefoxMinVersion": "FIREFOX_120",
    }


@pytest.fixture(name="check_ping_for_experiment")
def fixture_check_ping_for_experiment(trigger_experiment_loader):
    def _check_ping_for_experiment(experiment=None):
        control = True
        timeout = time.time() + 60 * 5
        while control and time.time() < timeout:
            data = requests.get("http://ping-server:5000/pings").json()
            experiments_data = [
                item["environment"]["experiments"]
                for item in data
                if "experiments" in item["environment"]
            ]
            for item in experiments_data:
                if experiment in item:
                    return True
            time.sleep(5)
            trigger_experiment_loader()
        return False

    return _check_ping_for_experiment


@pytest.fixture(name="telemetry_event_check")
def fixture_telemetry_event_check(trigger_experiment_loader):
    def _telemetry_event_check(experiment=None, event=None):
        telemetry = requests.get("http://ping-server:5000/pings").json()
        events = [
            event["payload"]["events"]["parent"]
            for event in telemetry
            if "events" in event["payload"] and "parent" in event["payload"]["events"]
        ]

        try:
            for _event in events:
                for item in _event:
                    if (experiment and event) in item:
                        return True
            raise AssertionError
        except (AssertionError, TypeError):
            trigger_experiment_loader()
            return False

    return _telemetry_event_check


@pytest.fixture
def demo_app(selenium, experiment_url):
    return DemoAppPage(selenium, experiment_url)
