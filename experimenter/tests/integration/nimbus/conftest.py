import logging
import os
import time
import uuid
from pathlib import Path
from urllib.parse import urljoin

import pytest
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from selenium import webdriver
from selenium.webdriver.firefox.service import Service

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

APPLICATION_SELECT_VALUE = {
    BaseExperimentApplications.FIREFOX_DESKTOP.value: "firefox-desktop",
    BaseExperimentApplications.FIREFOX_FENIX.value: "fenix",
    BaseExperimentApplications.FIREFOX_IOS.value: "ios",
    BaseExperimentApplications.FOCUS_ANDROID.value: "focus-android",
    BaseExperimentApplications.FOCUS_IOS.value: "focus-ios",
    BaseExperimentApplications.DEMO_APP.value: "demo-app",
}


def slugify(name):
    return name.lower().replace(" ", "-").replace("[", "").replace("]", "")


@pytest.fixture(name="application_feature_ids")
def fixture_application_feature_ids():
    return {
        BaseExperimentApplications.FIREFOX_DESKTOP.value: helpers.get_feature_id_as_string(  #  NOQA
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
    firefox_options.set_preference("remote.system-access-check.enabled", False)
    firefox_options.add_argument("-remote-allow-system-access")
    return firefox_options


@pytest.fixture
def selenium(selenium, experiment_slug, kinto_client):
    script = """Services.fog.testResetFOG();"""
    with selenium.context(selenium.CONTEXT_CHROME):
        selenium.execute_script(script)

    yield selenium

    if os.getenv("CIRCLECI") is None:
        try:
            helpers.end_experiment(experiment_slug)
            kinto_client.approve()
        except Exception:
            pass


@pytest.fixture
def driver(firefox_options):
    firefox_service = Service("/usr/bin/geckodriver")
    driver = webdriver.Firefox(service=firefox_service, options=firefox_options)
    yield driver
    driver.quit()


@pytest.fixture(
    # Use all applications as available parameters in circle config
    params=list(BaseExperimentApplications),
    ids=[application.name for application in BaseExperimentApplications],
)
def application(request):
    return request.param.value


@pytest.fixture(
    params=[False, True],
)
def use_group_id(request):
    return request.param


@pytest.fixture(scope="session")
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
    kinto_url = os.getenv("INTEGRATION_TEST_KINTO_URL", "http://kinto:8888/v1")
    return KintoClient(
        APPLICATION_KINTO_COLLECTION[default_data.application], server_url=kinto_url
    )


@pytest.fixture
def archived_tab_url(base_url):
    return f"{base_url}?status=Archived"


@pytest.fixture
def drafts_tab_url(base_url):
    return f"{base_url}?status=Draft"


@pytest.fixture
def experiment_name(request):
    return f"{request.node.name[:75]}{str(uuid.uuid4())[:4]}"


@pytest.fixture
def experiment_slug(experiment_name):
    return slugify(experiment_name)


@pytest.fixture
def experiment_url(base_url, experiment_slug):
    return f"{urljoin(base_url, experiment_slug)}/summary/"


@pytest.fixture
def old_base_url():
    return f"{os.getenv('INTEGRATION_TEST_NGINX_URL', 'https://nginx')}/nimbus"


@pytest.fixture(name="load_experiment_outcomes")
def fixture_load_experiment_outcomes():
    """Fixture to create a list of outcomes based on the current configs."""
    outcomes = {"firefox_desktop": "", "fenix": "", "firefox_ios": ""}
    parent_path = Path(__file__).parents[3]
    base_path = (
        parent_path
        / "experimenter"
        / "outcomes"
        / "metric-hub-main"
        / "jetstream"
        / "outcomes"
    )

    for k in list(outcomes):
        outcomes[k] = [
            name.split("_")[0].rsplit(".")[0]
            for name in os.listdir(f"{base_path}/{k}")
            if "example" not in name
        ]
    return outcomes


@pytest.fixture
def default_data(
    application, application_feature_ids, experiment_name, load_experiment_outcomes
):
    feature_config_id = application_feature_ids[application]

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
            targeting="no_targeting",
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
        languages=False,
        countries=False,
        is_rollout=False,
        reference_branch_value="{}",
        treatment_branch_value="{}",
    ):
        home = HomePage(selenium, base_url).open()
        home.create_new_button()
        home.public_name = default_data.public_name
        home.hypothesis = default_data.hypothesis
        home.application = APPLICATION_SELECT_VALUE[default_data.application]

        # Fill Overview Page
        summary = home.save_and_continue()
        overview = summary.navigate_to_overview()
        overview.select_risk_brand_false()
        overview.select_risk_message_false()
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
            assert metrics.secondary_outcomes.text != "", (
                "The seconday outcome was not set"
            )

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
        else:
            if languages:
                audience.languages = ["English"]
            if countries:
                audience.countries = ["Canada"]

        return audience.save_and_continue()

    return _create_experiment


@pytest.fixture
def trigger_experiment_loader(selenium):
    def _trigger_experiment_loader():
        with selenium.context(selenium.CONTEXT_CHROME):
            script = """
                const callback = arguments[0];

                (async function () {
                    try {
                        const { ExperimentAPI } = ChromeUtils.importESModule("resource://nimbus/ExperimentAPI.sys.mjs");
                        const { RemoteSettings } = ChromeUtils.importESModule("resource://services-settings/remote-settings.sys.mjs");

                        await RemoteSettings.pollChanges();
                        await ExperimentAPI.ready();
                        await ExperimentAPI._rsLoader.updateRecipes("test");

                        callback(true);
                    } catch (err) {
                        callback(false);
                    }
                })();
                """
            selenium.execute_async_script(script)
        time.sleep(5)

    return _trigger_experiment_loader


@pytest.fixture()
def default_data_api(application, application_feature_ids):
    feature_config_id = application_feature_ids[application]
    return {
        "hypothesis": "Test Hypothesis",
        "application": application,
        "changelogMessage": "test updates",
        "targetingConfigSlug": "no_targeting",
        "publicDescription": "Some sort of Fancy Words",
        "riskRevenue": False,
        "riskPartnerRelated": False,
        "riskBrand": False,
        "riskMessage": False,
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


@pytest.fixture(name="telemetry_event_check")
def fixture_telemetry_event_check(trigger_experiment_loader, selenium):
    def _telemetry_event_check(experiment=None, event=None):
        nimbus_events = None
        try:
            with selenium.context(selenium.CONTEXT_CHROME):
                if event == "enrollment":
                    nimbus_events = selenium.execute_script(
                        """
                            return Glean.nimbusEvents.enrollment.testGetValue("events")
                        """
                    )
                elif event == "unenrollment":
                    nimbus_events = selenium.execute_script(
                        """
                            return Glean.nimbusEvents.unenrollment.testGetValue("events")
                        """
                    )
            logging.info(f"nimbus events: {nimbus_events}")
            assert any(events.get("name", {}) == event for events in nimbus_events)
            assert any(
                events.get("extra", {}).get("experiment") == experiment
                for events in nimbus_events
            )
            return True
        except (AssertionError, TypeError):
            trigger_experiment_loader()
            return False

    return _telemetry_event_check


@pytest.fixture
def demo_app(selenium, experiment_url):
    return DemoAppPage(selenium, experiment_url)
