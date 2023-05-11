import unittest

from ..cirrus.sdk import SDK


class SDKTestCase(unittest.TestCase):
    def test_compute_enrollments(self):
        sdk = SDK()
        recipes = [
            {"id": 1, "name": "recipe1"},
            {"id": 2, "name": "recipe2"},
        ]
        targeting_context = {"client_id": "testid"}

        result = sdk.compute_enrollments(recipes, targeting_context)
        self.assertEqual(result, [])
