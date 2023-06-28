from unittest.mock import MagicMock, patch

import pytest
import requests


def test_get_recipes_is_empty(remote_settings):
    assert remote_settings.get_recipes() == {"data": []}


def test_update_recipes(remote_settings):
    new_recipes = {"data": [{"experiment1": True}, {"experiment2": False}]}
    remote_settings.update_recipes(new_recipes)
    assert remote_settings.get_recipes() == new_recipes


@patch("cirrus.experiment_recipes.requests.get")
def test_empty_data_key(mock_get, remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mock_get.return_value = mock_response

    remote_settings.fetch_recipes()
    assert remote_settings.get_recipes() == {"data": []}


@patch("cirrus.experiment_recipes.requests.get")
def test_non_empty_data_key(mock_get, remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [{"experiment1": True}, {"experiment2": False}]
    }
    mock_get.return_value = mock_response

    remote_settings.fetch_recipes()
    assert remote_settings.get_recipes() == {
        "data": [{"experiment1": True}, {"experiment2": False}]
    }


@patch("cirrus.experiment_recipes.requests.get")
def test_successful_response(mock_get, remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mock_get.return_value = mock_response

    remote_settings.fetch_recipes()
    mock_get.assert_called_once_with(remote_settings.url)


@patch("cirrus.experiment_recipes.requests.get")
def test_failed_request(mock_get, remote_settings):
    mock_get.side_effect = requests.exceptions.RequestException("Failed request")

    with pytest.raises(requests.exceptions.RequestException) as context:
        remote_settings.fetch_recipes()

        assert str(context.value) == "Failed request"
    assert remote_settings.get_recipes() == {"data": []}


@patch("cirrus.experiment_recipes.requests.get")
def test_empty_data_key_with_non_empty_recipes(mock_get, remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mock_get.return_value = mock_response

    remote_settings.update_recipes({"data": [{"experiment1": True}]})
    remote_settings.fetch_recipes()
    assert remote_settings.get_recipes() == {"data": [{"experiment1": True}]}
