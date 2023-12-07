import json
import time
from functools import lru_cache

import requests

from nimbus.models.base_dataclass import (
    BaseExperimentApplications,
)

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

            time.sleep(LOAD_DATA_RETRY_DELAY)


@lru_cache(maxsize=None)
def load_config_data():
    return load_graphql_data(
        {
            "operationName": "getConfig",
            "variables": {},
            "query": """
                query getConfig {
                    nimbusConfig {
                        applications {
                            label
                            value
                        }
                        channels {
                            label
                            value
                        }
                        conclusionRecommendations {
                            label
                            value
                        }
                        applicationConfigs {
                            application
                            channels {
                                label
                                value
                            }
                        }
                        allFeatureConfigs {
                            id
                            name
                            slug
                            description
                            application
                            ownerEmail
                            schema
                            setsPrefs
                            enabled
                        }
                        firefoxVersions {
                            label
                            value
                        }
                        outcomes {
                            friendlyName
                            slug
                            application
                            description
                            isDefault
                            metrics {
                                slug
                                friendlyName
                                description
                            }
                        }
                        owners {
                            username
                        }
                        targetingConfigs {
                            label
                            value
                            description
                            applicationValues
                            stickyRequired
                            isFirstRunRequired
                        }
                        hypothesisDefault
                        documentationLink {
                            label
                            value
                        }
                        maxPrimaryOutcomes
                        locales {
                            id
                            code
                            name
                        }
                        countries {
                            id
                            code
                            name
                        }
                        languages {
                            id
                            code
                            name
                        }
                        projects {
                            id
                            name
                        }
                        takeaways {
                            label
                            value
                        }
                        types {
                            label
                            value
                        }
                        statusUpdateExemptFields {
                            all
                            experiments
                            rollouts
                        }
                        populationSizingData
                    }
                }
                """,
        }
    )["data"]["nimbusConfig"]


def load_targeting_configs(app=BaseExperimentApplications.FIREFOX_DESKTOP.value):
    config_data = load_config_data()
    return [
        item["value"]
        for item in config_data["targetingConfigs"]
        if BaseExperimentApplications.FIREFOX_DESKTOP.value in app
        and BaseExperimentApplications.FIREFOX_DESKTOP.value in item["applicationValues"]
        or BaseExperimentApplications.FIREFOX_DESKTOP.value not in app
        and BaseExperimentApplications.FIREFOX_DESKTOP.value
        not in item["applicationValues"]
    ]


def get_feature_id_as_string(slug, app):
    config_data = load_config_data()["allFeatureConfigs"]
    for f in config_data:
        if f["slug"] == slug and f["application"] == app:
            return str(f["id"])


def load_experiment_data(slug):
    return load_graphql_data(
        {
            "operationName": "getExperiment",
            "variables": {"slug": slug},
            "query": """
                query getExperiment($slug: String!) {
                    experimentBySlug(slug: $slug) {
                        id
                        jexlTargetingExpression
                        recipeJson
                    }
                }
            """,
        }
    )


def create_basic_experiment(name, app, targeting=None, languages=None, is_rollout=False):
    config_data = load_config_data()

    if languages is None:
        languages = []
    language_ids = [l["id"] for l in config_data["languages"] if l["code"] in languages]

    if targeting is None:
        targeting = load_targeting_configs()[0]

    return load_graphql_data(
        {
            "operationName": "createExperiment",
            "variables": {
                "input": {
                    "name": name,
                    "hypothesis": "Test hypothesis",
                    "application": app,
                    "languages": language_ids,
                    "changelogMessage": "test changelog message",
                    "targetingConfigSlug": targeting,
                    "isRollout": is_rollout,
                }
            },
            "query": """
                mutation createExperiment($input: ExperimentInput!) {
                    createExperiment(input: $input) {
                        nimbusExperiment {
                            slug
                        }
                    }
                }
            """,
        }
    )


def update_experiment(slug, data):
    experiment_id = load_experiment_data(slug)["data"]["experimentBySlug"]["id"]
    data.update({"id": experiment_id})
    return load_graphql_data(
        {
            "operationName": "updateExperiment",
            "variables": {"input": data},
            "query": """
                mutation updateExperiment($input: ExperimentInput!) {
                    updateExperiment(input: $input) {
                        message
                    }
                }
            """,
        }
    )


def create_experiment(slug, app, data, targeting=None, is_rollout=False):
    return (
        create_basic_experiment(
            slug,
            app,
            targeting=targeting,
            is_rollout=is_rollout,
        ),
        update_experiment(slug, data),
    )


def end_experiment(slug):
    experiment_id = load_experiment_data(slug)["data"]["experimentBySlug"]["id"]

    data = {
        "id": experiment_id,
        "changelogMessage": "Update Experiment",
        "publishStatus": "APPROVED",
        "status": "LIVE",
        "statusNext": "COMPLETE",
    }

    load_graphql_data(
        {
            "operationName": "updateExperiment",
            "variables": {"input": data},
            "query": """
                mutation updateExperiment($input: ExperimentInput!) {
                    updateExperiment(input: $input) {
                        message
                    }
                }
            """,
        }
    )
