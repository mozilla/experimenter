import json

import pytest
from cirrus_sdk import NimbusError

from cirrus.sdk import SDK


class TestSdk:
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
    def test_invalid_context(self, context, expected_error_message):
        with pytest.raises(NimbusError) as e:
            SDK(context=context)

        assert str(e.value).startswith(expected_error_message)

    def test_compute_enrollments(self, sdk):
        targeting_context = {"clientId": "test", "requestContext": {}}

        result = sdk.compute_enrollments(targeting_context)
        assert result == {
            "enrolledFeatureConfigMap": {},
            "enrollments": [],
            "events": [],
        }

    def test_failure_case_no_client_id_key(self, sdk):
        targeting_context = {"requestContext": {}}

        try:
            result = sdk.compute_enrollments(targeting_context)
        except NimbusError:
            self.fail("NimbusError was raised when it should not have been")
        assert result == {}

    def test_failure_case_no_client_id_value(self, sdk):
        targeting_context = {"clientId": None, "requestContext": {}}

        try:
            result = sdk.compute_enrollments(targeting_context)
        except NimbusError:
            self.fail("NimbusError was raised when it should not have been")
        assert result == {}

    def test_failure_case_no_request_context(self, sdk):
        targeting_context = {"clientId": "test"}

        try:
            result = sdk.compute_enrollments(targeting_context)
        except NimbusError:
            self.fail("NimbusError was raised when it should not have been")
        assert result == {}

    def test_set_experiments_recipe_both_empty(self, sdk):
        recipes = "{}"
        targeting_context = {}
        sdk.set_experiments(recipes)
        result = sdk.compute_enrollments(targeting_context)
        assert result == {}

    def test_set_experiments_success(self, sdk):
        recipes = '{"data": [{"experiment1": True}, {"experiment2": False}]}'
        targeting_context = {"clientId": "test", "requestContext": {}}
        sdk.set_experiments(recipes)
        result = sdk.compute_enrollments(targeting_context)
        assert result == {
            "enrolledFeatureConfigMap": {},
            "enrollments": [],
            "events": [],
        }

    def test_set_experiments_failure_missing_data_key(self, sdk):
        recipes = '{"invalid": []}'

        targeting_context = {"clientId": "test", "requestContext": {}}
        sdk.set_experiments(recipes)
        result = sdk.compute_enrollments(targeting_context)
        assert result == {
            "enrolledFeatureConfigMap": {},
            "enrollments": [],
            "events": [],
        }

    def test_set_experiments_failure_malform_key(self, sdk):
        recipes = '{"invalid}'

        targeting_context = {"clientId": "test", "requestContext": {}}
        sdk.set_experiments(recipes)
        result = sdk.compute_enrollments(targeting_context)
        assert result == {
            "enrolledFeatureConfigMap": {},
            "enrollments": [],
            "events": [],
        }
