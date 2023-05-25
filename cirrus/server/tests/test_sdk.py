import unittest

from cirrus_sdk import NimbusError

from cirrus.sdk import SDK


class SDKTestCase(unittest.TestCase):
    def test_compute_enrollments(self):
        sdk = SDK()
        targeting_context = {"clientId": "test", "requestContext": {}}

        result = sdk.compute_enrollments(targeting_context)
        self.assertEqual(
            result, {"enrolledFeatureConfigMap": {}, "enrollments": [], "events": []}
        )

    def test_failure_case_no_client_id_key(self):
        sdk = SDK()
        targeting_context = {"requestContext": {}}

        try:
            result = sdk.compute_enrollments(targeting_context)
        except NimbusError:
            self.fail("NimbusError was raised when it should not have been")
        self.assertEqual(result, {})

    def test_failure_case_no_client_id_value(self):
        sdk = SDK()
        targeting_context = {"clientId": None, "requestContext": {}}

        try:
            result = sdk.compute_enrollments(targeting_context)
        except NimbusError:
            self.fail("NimbusError was raised when it should not have been")
        self.assertEqual(result, {})

    def test_failure_case_no_request_context(self):
        sdk = SDK()
        targeting_context = {"clientId": "test"}

        try:
            result = sdk.compute_enrollments(targeting_context)
        except NimbusError:
            self.fail("NimbusError was raised when it should not have been")
        self.assertEqual(result, {})

    def test_set_experiments_recipe_both_empty(self):
        sdk = SDK()
        recipes = "{}"
        targeting_context = {}
        sdk.set_experiments(recipes)
        result = sdk.compute_enrollments(targeting_context)
        self.assertEqual(result, {})

    def test_set_experiments_success(self):
        sdk = SDK()
        recipes = '{"data": [{"experiment1": True}, {"experiment2": False}]}'
        targeting_context = {"clientId": "test", "requestContext": {}}
        sdk.set_experiments(recipes)
        result = sdk.compute_enrollments(targeting_context)
        self.assertEqual(
            result, {"enrolledFeatureConfigMap": {}, "enrollments": [], "events": []}
        )

    def test_set_experiments_failure_missing_data_key(self):
        sdk = SDK()
        recipes = '{"invalid": []}'

        targeting_context = {"clientId": "test", "requestContext": {}}
        sdk.set_experiments(recipes)
        result = sdk.compute_enrollments(targeting_context)
        self.assertEqual(
            result, {"enrolledFeatureConfigMap": {}, "enrollments": [], "events": []}
        )

    def test_set_experiments_failure_malform_key(self):
        sdk = SDK()
        recipes = '{"invalid}'

        targeting_context = {"clientId": "test", "requestContext": {}}
        sdk.set_experiments(recipes)
        result = sdk.compute_enrollments(targeting_context)
        self.assertEqual(
            result, {"enrolledFeatureConfigMap": {}, "enrollments": [], "events": []}
        )
