import json
import unittest

from cirrus_sdk import NimbusError
from parameterized import parameterized

from cirrus.sdk import SDK
from cirrus.settings import context


class SDKTestCase(unittest.TestCase):
    def setUp(self):
        self.sdk = SDK(context=context)

    @parameterized.expand(
        [
            [
                json.dumps(
                    {  # missing app_id
                        "app_name": "test_name",
                        "channel": "test_channel",
                    }
                ),
                "NimbusError.JsonError('JSON Error: missing field `app_id`",
            ],
            [
                json.dumps(
                    {  # missing app_name
                        "app_id": "test_id",
                        "channel": "test_channel",
                    }
                ),
                "NimbusError.JsonError('JSON Error: missing field `app_name`",
            ],
            [
                json.dumps(
                    {  # missing channel
                        "app_id": "test_id",
                        "app_name": "test_app_name",
                    }
                ),
                "NimbusError.JsonError('JSON Error: missing field `channel`",
            ],
        ]
    )
    def test_invalid_context(self, context, expected_error_message):
        with self.assertRaises(NimbusError) as e:
            SDK(context=context)

        self.assertTrue(str(e.exception).startswith(expected_error_message))

    def test_compute_enrollments(self):
        targeting_context = {"clientId": "test", "requestContext": {}}

        result = self.sdk.compute_enrollments(targeting_context)
        self.assertEqual(
            result, {"enrolledFeatureConfigMap": {}, "enrollments": [], "events": []}
        )

    def test_failure_case_no_client_id_key(self):
        targeting_context = {"requestContext": {}}

        try:
            result = self.sdk.compute_enrollments(targeting_context)
        except NimbusError:
            self.fail("NimbusError was raised when it should not have been")
        self.assertEqual(result, {})

    def test_failure_case_no_client_id_value(self):
        targeting_context = {"clientId": None, "requestContext": {}}

        try:
            result = self.sdk.compute_enrollments(targeting_context)
        except NimbusError:
            self.fail("NimbusError was raised when it should not have been")
        self.assertEqual(result, {})

    def test_failure_case_no_request_context(self):
        targeting_context = {"clientId": "test"}

        try:
            result = self.sdk.compute_enrollments(targeting_context)
        except NimbusError:
            self.fail("NimbusError was raised when it should not have been")
        self.assertEqual(result, {})

    def test_set_experiments_recipe_both_empty(self):
        recipes = "{}"
        targeting_context = {}
        self.sdk.set_experiments(recipes)
        result = self.sdk.compute_enrollments(targeting_context)
        self.assertEqual(result, {})

    def test_set_experiments_success(self):
        recipes = '{"data": [{"experiment1": True}, {"experiment2": False}]}'
        targeting_context = {"clientId": "test", "requestContext": {}}
        self.sdk.set_experiments(recipes)
        result = self.sdk.compute_enrollments(targeting_context)
        self.assertEqual(
            result, {"enrolledFeatureConfigMap": {}, "enrollments": [], "events": []}
        )

    def test_set_experiments_failure_missing_data_key(self):
        recipes = '{"invalid": []}'

        targeting_context = {"clientId": "test", "requestContext": {}}
        self.sdk.set_experiments(recipes)
        result = self.sdk.compute_enrollments(targeting_context)
        self.assertEqual(
            result, {"enrolledFeatureConfigMap": {}, "enrollments": [], "events": []}
        )

    def test_set_experiments_failure_malform_key(self):
        recipes = '{"invalid}'

        targeting_context = {"clientId": "test", "requestContext": {}}
        self.sdk.set_experiments(recipes)
        result = self.sdk.compute_enrollments(targeting_context)
        self.assertEqual(
            result, {"enrolledFeatureConfigMap": {}, "enrollments": [], "events": []}
        )
