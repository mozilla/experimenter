import unittest
from unittest.mock import patch

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

    def test_set_experiments_success(self):
        sdk = SDK()
        recipes = '{"data": []}'

        with patch.object(sdk.client, "set_experiments") as mock_set_experiments:
            sdk.set_experiments(recipes)

        mock_set_experiments.assert_called_once_with(recipes)

    def test_set_experiments_failure(self):
        sdk = SDK()
        recipes = '{"data": []}'

        with patch.object(sdk.client, "set_experiments") as mock_set_experiments:
            mock_set_experiments.side_effect = NimbusError("Failed to set experiments")
            sdk.set_experiments(recipes)

        mock_set_experiments.assert_called_once_with(recipes)

    def test_set_experiments_failure_missing_data_key(self):
        sdk = SDK()
        recipes = '{"invalid_key": []}'

        with patch.object(sdk.client, "set_experiments") as mock_set_experiments:
            try:
                sdk.set_experiments(recipes)
            except NimbusError:
                self.fail("No Nimbus exception should have been raised")

        mock_set_experiments.assert_called_once_with(recipes)
