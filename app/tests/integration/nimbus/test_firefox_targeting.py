import json
import time

import pytest
import requests
from nimbus.pages.browser import Browser
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
    experiment_name,
    targeting_config_slug,
    create_desktop_experiment,
):
    targeting = helpers.load_targeting_configs()[1]
    experiment_slug = str(slugify(experiment_name))
    data = {
        "hypothesis": "Test Hypothesis",
        "application": "DESKTOP",
        "changelogMessage": "test updates",
        "targetingConfigSlug": targeting,
        "publicDescription": "Some sort of Fancy Words",
        "riskRevenue": False,
        "riskPartnerRelated": False,
        "riskBrand": False,
        "featureConfigId": 1,
        "referenceBranch": {
            "description": "reference branch",
            "name": "Branch 1",
            "ratio": 50,
            "featureEnabled": True,
            "featureValue": "{}",
        },
        "treatmentBranches": [
            {
                "description": "treatment branch",
                "name": "Branch 2",
                "ratio": 50,
                "featureEnabled": False,
                "featureValue": "",
            }
        ],
        "populationPercent": "100",
        "totalEnrolledClients": 55,
    }
    create_desktop_experiment(
        experiment_slug,
        "desktop",
        targeting_config_slug,
        data,
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
