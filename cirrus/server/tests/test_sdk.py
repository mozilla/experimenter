import unittest

from ..cirrus.sdk import SDK


class SDKTestCase(unittest.TestCase):
    def test_compute_enrollments(self):
        # Create instance of SDK class
        sdk = SDK()

        # Create test input data
        recipes = [
            {"id": 1, "name": "recipe1"},
            {"id": 2, "name": "recipe2"},
        ]
        targeting_context = {"client_id": "testid"}

        # Call method with test input data
        result = sdk.compute_enrollments(recipes, targeting_context)

        # Verify that method returns expected output
        self.assertEqual(result, [])
