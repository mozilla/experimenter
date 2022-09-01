import json
import os
import uuid
from pathlib import Path
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

APPLICATION_FEATURE_IDS = {
    BaseExperimentApplications.DESKTOP: "1",
    BaseExperimentApplications.FENIX: "2",
    BaseExperimentApplications.IOS: "3",
    BaseExperimentApplications.FOCUS_ANDROID: "4",
    BaseExperimentApplications.FOCUS_IOS: "6",
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
    feature_config_id = APPLICATION_FEATURE_IDS[application]

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
        metrics=BaseExperimentMetricsDataClass(
            primary_outcomes=[], secondary_outcomes=[]
        ),
        audience=BaseExperimentAudienceDataClass(
            channel=BaseExperimentAudienceChannels.RELEASE,
            min_version=80,
            targeting="no_targeting",
            percentage=50.0,
            expected_clients=50,
            locale=None,
            countries=None,
            languages=None,
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
        branches.feature_config = default_data.feature_config_id
        branches.reference_branch_description = default_data.branches[0].description
        branches.treatment_branch_description = default_data.branches[1].description

        if default_data.application.value == "DESKTOP":
            branches.reference_branch_enabled.click()
            branches.treatment_branch_enabled.click()

        branches.reference_branch_value = "{}"
        branches.treatment_branch_value = "{}"

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
def create_basic_experiment():
    def _create_basic_experiment(name, app, targeting, languages=[]):
        query = {
            "operationName": "createExperiment",
            "variables": {
                "input": {
                    "name": name,
                    "hypothesis": "Test hypothesis",
                    "application": app.upper(),
                    "languages": languages,
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

    return _create_basic_experiment


@pytest.fixture
def create_desktop_experiment(create_basic_experiment):
    def _create_desktop_experiment(slug, app, targeting, **data):
        # create a basic experiment via graphql so we can get an ID
        create_basic_experiment(
            slug,
            app,
            targeting,
        )

        # Get experiment ID
        get_id_query = {
            "operationName": "getExperiment",
            "variables": {"slug": f"{slug}"},
            "query": """
                    query getExperiment($slug: String!) {
                        experimentBySlug(slug: $slug) {
                            id
                        }
                    }
                    """,
        }

        response = requests.post(
            "https://nginx/api/v5/graphql", json=get_id_query, verify=False
        )
        experiment_id = response.json()["data"]["experimentBySlug"]["id"]

        query = {
            "operationName": "updateExperiment",
            "variables": {
                "input": {
                    "id": experiment_id,
                    "name": f"test_check_telemetry_enrollment-{experiment_id}",
                    "hypothesis": "Test hypothesis",
                    "application": app.upper(),
                    "changelogMessage": "test updated",
                    "targetingConfigSlug": targeting,
                    "publicDescription": data.get("public_description", "Fancy Words"),
                    "riskRevenue": data.get("risk_revenue"),
                    "riskPartnerRelated": data.get("risk_partner_related"),
                    "riskBrand": data.get("risk_brand"),
                    "featureConfigId": data.get("feature_config"),
                    "referenceBranch": data.get("reference_branch"),
                    "treatmentBranches": data.get("treatement_branch"),
                    "populationPercent": data.get("population_percent"),
                    "totalEnrolledClients": data.get("total_enrolled_clients"),
                }
            },
            "query": "mutation updateExperiment($input: ExperimentInput!) \
                {\n updateExperiment(input: $input) \
                    {\n message\n __typename\n }\n}\n",
        }
        requests.post("https://nginx/api/v5/graphql", json=query, verify=False)

    return _create_desktop_experiment


@pytest.fixture(name="language_database_id_loader")
def fixture_language_database_id_loader():
    """Return database id's for languages"""

    def _language_database_id_loader(languages=None):
        language_list = []
        path = Path().resolve()
        path = str(path)
        path = path.strip("/tests/integration/nimbus")
        path = os.path.join("/", path, "experimenter/base/fixtures/languages.json")
        with open(path) as file:
            data = json.loads(file.read())
            for language in languages:
                for item in data:
                    if language in item["fields"]["code"][:2]:
                        language_list.append(item["pk"])
        return language_list

    return _language_database_id_loader


@pytest.fixture
def trigger_experiment_loader(selenium):
    def _trigger_experiment_loader():
        with selenium.context(selenium.CONTEXT_CHROME):
            selenium.execute_script(
                """
                    ChromeUtils.import(
                        "resource://nimbus/lib/RemoteSettingsExperimentLoader.jsm"
                    ).RemoteSettingsExperimentLoader.updateRecipes();
                """
            )

    return _trigger_experiment_loader
