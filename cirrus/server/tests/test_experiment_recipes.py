import unittest
from unittest.mock import MagicMock, patch

import requests

from ..cirrus.experiment_recipes import RemoteSettings


class TestFetchRecipes(unittest.TestCase):
    def get_remote_settings(self):
        return RemoteSettings()

    def test_get_recipes_is_empty(self):
        rs = self.get_remote_settings()
        assert rs.get_recipes() == []

    def test_update_recipes(self):
        rs = self.get_remote_settings()
        new_recipes = [{"experiment1": True}, {"experiment2": False}]
        rs.update_recipes(new_recipes)
        assert rs.get_recipes() == new_recipes

    @patch("requests.get")
    def test_empty_data_key(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        rs = self.get_remote_settings()
        rs.fetch_recipes()
        self.assertEqual(rs.get_recipes(), [])

    @patch("requests.get")
    def test_non_empty_data_key(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"experiment1": True}, {"experiment2": False}]
        }
        mock_get.return_value = mock_response

        rs = self.get_remote_settings()
        rs.fetch_recipes()
        self.assertEqual(
            rs.get_recipes(), [{"experiment1": True}, {"experiment2": False}]
        )

    @patch("requests.get")
    def test_successful_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        rs = self.get_remote_settings()
        rs.fetch_recipes()
        mock_get.assert_called_once_with(rs.url)

    @patch("requests.get")
    def test_failed_request(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Failed request")

        rs = RemoteSettings()
        try:
            rs.fetch_recipes()
        except requests.exceptions.RequestException as e:
            # Assert that the exception is the expected exception
            self.assertEqual(str(e), "Failed request")
        else:
            # If no exception was raised, fail the test case
            self.fail("Expected RequestException but no exception was raised")

        # Assert that the recipes are empty
        self.assertEqual(rs.get_recipes(), [])

    @patch("requests.get")
    def test_empty_data_key_with_non_empty_recipes(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        rs = self.get_remote_settings()
        rs.update_recipes([{"experiment1": True}])
        rs.fetch_recipes()
        self.assertEqual(rs.get_recipes(), [{"experiment1": True}])
