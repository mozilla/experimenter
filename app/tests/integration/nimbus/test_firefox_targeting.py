import json
import time

import pytest
import requests
from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.pages.browser import Browser


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
    default_data,
    create_experiment,
    targeting_config_slug,
):
    # TODO #6791
    # If the targeting config slug includes the word desktop it will cause this test
    # to run against applications other than desktop, which will then fail.
    # This check will prevent the test from executing fully but we should dig
    # into preventing this case altogether when we have time.
    if default_data.application != BaseExperimentApplications.DESKTOP:
        return

    default_data.audience.targeting = targeting_config_slug
    experiment = create_experiment(selenium)

    experiment_data = load_experiment_data(experiment.experiment_slug)
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
