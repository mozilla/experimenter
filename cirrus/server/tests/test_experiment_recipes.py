from unittest.mock import MagicMock, patch

import pytest
import requests


class TestFetchRecipes:
    def test_get_recipes_is_empty(self, remote_setting):
        rs = remote_setting
        assert rs.get_recipes() == {"data": []}

    def test_update_recipes(self, remote_setting):
        rs = remote_setting
        new_recipes = {"data": [{"experiment1": True}, {"experiment2": False}]}
        rs.update_recipes(new_recipes)
        assert rs.get_recipes() == new_recipes

    @patch("cirrus.experiment_recipes.requests.get")
    def test_empty_data_key(self, mock_get, remote_setting):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        rs = remote_setting
        rs.fetch_recipes()
        assert rs.get_recipes() == {"data": []}

    @patch("cirrus.experiment_recipes.requests.get")
    def test_non_empty_data_key(self, mock_get, remote_setting):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"experiment1": True}, {"experiment2": False}]
        }
        mock_get.return_value = mock_response

        rs = remote_setting
        rs.fetch_recipes()
        assert rs.get_recipes() == {
            "data": [{"experiment1": True}, {"experiment2": False}]
        }

    @patch("cirrus.experiment_recipes.requests.get")
    def test_successful_response(self, mock_get, remote_setting):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        rs = remote_setting
        rs.fetch_recipes()
        mock_get.assert_called_once_with(rs.url)

    @patch("cirrus.experiment_recipes.requests.get")
    def test_failed_request(self, mock_get, remote_setting):
        mock_get.side_effect = requests.exceptions.RequestException("Failed request")

        rs = remote_setting

        with pytest.raises(requests.exceptions.RequestException) as context:
            rs.fetch_recipes()

        assert str(context.value) == "Failed request"
        assert rs.get_recipes() == {"data": []}

    @patch("cirrus.experiment_recipes.requests.get")
    def test_empty_data_key_with_non_empty_recipes(self, mock_get, remote_setting):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        rs = remote_setting
        rs.update_recipes({"data": [{"experiment1": True}]})
        rs.fetch_recipes()
        assert rs.get_recipes() == {"data": [{"experiment1": True}]}
