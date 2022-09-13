import json
import time
from urllib.parse import urljoin

import pytest
import requests
from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.pages.browser import Browser
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.utils import helpers

LOAD_DATA_RETRIES = 10
LOAD_DATA_RETRY_DELAY = 1.0


def load_graphql_data(query):
    for retry in range(LOAD_DATA_RETRIES):
        try:
            return requests.post(
                "https://nginx/api/v5/graphql",
                json=query,
                verify=False,
            ).json()
        except json.JSONDecodeError:
            if retry + 1 >= LOAD_DATA_RETRIES:
                raise
            else:
                time.sleep(LOAD_DATA_RETRY_DELAY)


def load_targeting_configs():
    data = load_graphql_data(
        {
            "operationName": "getConfig",
            "variables": {},
            "query": """
                    query getConfig {
                        nimbusConfig {
                            targetingConfigs {
                                label
                                value
                                applicationValues
                            }
                        }
                    }
                    """,
        }
    )
    targeting_configs = []
    for item in data["data"]["nimbusConfig"]["targetingConfigs"]:
        if "DESKTOP" in item["applicationValues"]:
            targeting_configs.append(item["value"])
    return targeting_configs


def load_experiment_data(slug):
    return load_graphql_data(
        {
            "operationName": "getExperiment",
            "variables": {"slug": slug},
            "query": """
                    query getExperiment($slug: String!) {
                        experimentBySlug(slug: $slug) {
                            jexlTargetingExpression
                            recipeJson
                            __typename
                        }
                    }
                    """,
        }
    )


@pytest.fixture(params=load_targeting_configs())
def targeting_config_slug(request):
    return request.param


@pytest.mark.run_targeting
def test_check_targeting(
    selenium,
    slugify,
    default_data,
    experiment_name,
    targeting_config_slug,
    create_desktop_experiment,
    countries_database_id_loader,
    locales_database_id_loader,
):
    targeting = helpers.load_targeting_configs()[1]
    experiment_slug = str(slugify(experiment_name))
    create_desktop_experiment(
        experiment_slug,
        "desktop",
        targeting_config_slug,
        public_description="Some sort of words",
        risk_revenue=False,
        risk_partner_related=False,
        risk_brand=False,
        feature_config=1,
        reference_branch={
            "description": "reference branch",
            "name": "Branch 1",
            "ratio": 50,
            "featureEnabled": True,
            "featureValue": "{}",
        },
        treatement_branch=[
            {
                "description": "treatment branch",
                "name": "Branch 2",
                "ratio": 50,
                "featureEnabled": False,
                "featureValue": "",
            }
        ],
        population_percent="75",
        total_enrolled_clients=35,
        channel="NIGHTLY",
        firefox_min_version="FIREFOX_100",
        firefox_max_version="FIREFOX_120",
        countries=countries_database_id_loader(["CA"]),
        proposed_enrollment="14",
        proposed_duration="30",
        locales=locales_database_id_loader(["en-CA"]),
    )
    experiment_data = load_experiment_data(experiment_slug)
    targeting = experiment_data["data"]["experimentBySlug"]["jexlTargetingExpression"]
    recipe = experiment_data["data"]["experimentBySlug"]["recipeJson"]

    # Inject filter expression
    selenium.get("about:blank")
    with open("nimbus/utils/filter_expression.js") as js:
        result = Browser.execute_script(
            selenium,
            targeting,
            json.dumps({"experiment": recipe}),
            script=js.read(),
            context="chrome",
        )
    assert result is not None, "Invalid Targeting, or bad recipe"
