import json
import time

import requests

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


def load_targeting_configs(app="DESKTOP"):
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
    return [
        item["value"]
        for item in data["data"]["nimbusConfig"]["targetingConfigs"]
        if "DESKTOP" in app
        and "DESKTOP" in item["applicationValues"]
        or "DESKTOP" not in app
        and "DESKTOP" not in item["applicationValues"]
    ]


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


def create_mobile_experiment(name, app, languages):
    query = {
        "operationName": "createExperiment",
        "variables": {
            "input": {
                "name": name,
                "hypothesis": "Test hypothesis",
                "application": app.upper(),
                "languages": languages,
                "changelogMessage": "test changelog message",
            }
        },
        "query": "mutation createExperiment($input: ExperimentInput!) \
            {\n  createExperiment(input: $input) \
            {\n    message\n    nimbusExperiment \
            {\n      slug\n      __typename\n    }\n    __typename\n  }\
            \n}",
    }
    requests.post("https://nginx/api/v5/graphql", json=query, verify=False)
