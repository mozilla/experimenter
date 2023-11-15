import json

import pytest
from cirrus_sdk import NimbusError

from cirrus.sdk import SDK


@pytest.mark.parametrize(
    ("context", "expected_error_message"),
    [
        (
            json.dumps(
                {  # missing app_id
                    "app_name": "test_name",
                    "channel": "test_channel",
                }
            ),
            "NimbusError.JsonError('JSON Error: missing field `app_id`",
        ),
        (
            json.dumps(
                {  # missing app_name
                    "app_id": "test_id",
                    "channel": "test_channel",
                }
            ),
            "NimbusError.JsonError('JSON Error: missing field `app_name`",
        ),
        (
            json.dumps(
                {  # missing channel
                    "app_id": "test_id",
                    "app_name": "test_app_name",
                }
            ),
            "NimbusError.JsonError('JSON Error: missing field `channel`",
        ),
    ],
)
def test_invalid_context(context, expected_error_message, metrics_handler):
    with pytest.raises(NimbusError) as e:
        SDK(context=context, coenrolling_feature_ids=[], metrics_handler=metrics_handler)

        assert str(e.value).startswith(expected_error_message)


def test_compute_enrollments(sdk):
    targeting_context = {"clientId": "test", "requestContext": {}}

    result = sdk.compute_enrollments(targeting_context)
    assert result == {
        "enrolledFeatureConfigMap": {},
        "enrollments": [],
        "events": [],
    }


@pytest.mark.parametrize(
    "targeting_context",
    [
        ({"requestContext": {}}),
        ({"clientId": None, "requestContext": {}}),
        ({"clientId": "test"}),
    ],
)
def test_failure_cases(sdk, targeting_context):
    try:
        result = sdk.compute_enrollments(targeting_context)
    except NimbusError:
        pytest.fail("NimbusError was raised when it should not have been")
    assert result == {}


def test_set_experiments_recipe_both_empty(sdk):
    recipes = "{}"
    targeting_context = {}
    sdk.set_experiments(recipes)
    result = sdk.compute_enrollments(targeting_context)
    assert result == {}


def test_set_experiments_success(sdk):
    recipes = '{"data": [{"experiment1": True}, {"experiment2": False}]}'
    targeting_context = {"clientId": "test", "requestContext": {}}
    sdk.set_experiments(recipes)
    result = sdk.compute_enrollments(targeting_context)
    assert result == {
        "enrolledFeatureConfigMap": {},
        "enrollments": [],
        "events": [],
    }


@pytest.mark.parametrize(
    ("recipes"),
    [
        ('{"invalid": []}'),
        ('{"invalid}'),
    ],
)
def test_set_experiments_failure_invalid_malform_key(sdk, recipes):
    targeting_context = {"clientId": "test", "requestContext": {}}
    sdk.set_experiments(recipes)
    result = sdk.compute_enrollments(targeting_context)
    assert result == {
        "enrolledFeatureConfigMap": {},
        "enrollments": [],
        "events": [],
    }


def test_coenrolling_feature_recipes(recipes_with_coenrolling_features, metrics_handler):
    targeting_context = {"clientId": "test", "requestContext": {}}
    context = {"app_id": "org.mozilla.test", "app_name": "test_app", "channel": "release"}
    feature_id = "coenrolling-feature"
    sdk = SDK(
        context=json.dumps(context),
        coenrolling_feature_ids=[feature_id],
        metrics_handler=metrics_handler,
    )
    sdk.set_experiments(recipes_with_coenrolling_features)
    result = sdk.compute_enrollments(targeting_context)

    assert result["enrolledFeatureConfigMap"][feature_id]["feature"]["value"] == {
        "map": {
            "experiment-1": "experiment-1",
            "experiment-2": "experiment-2",
        }
    }
