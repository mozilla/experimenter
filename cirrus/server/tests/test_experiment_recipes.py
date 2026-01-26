from unittest.mock import MagicMock, patch

import pytest
import requests

from cirrus.experiment_recipes import RecipeType, RemoteSettings


def test_remote_settings_url_check():
    # check for no ValueError with changset api, and ValueError with records api
    RemoteSettings(
        url="http://kinto:8888/v1/buckets/main/collections/nimbus-web-experiments/changeset?_expected=0",
        sdk=None,
    )
    with pytest.raises(ValueError):
        RemoteSettings(
            url="http://kinto:8888/v1/buckets/main/collections/nimbus-web-experiments/records",
            sdk=None,
        )


@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_get_recipes_is_empty(remote_settings):
    assert remote_settings.get_recipes() == {"data": []}


@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_update_recipes(remote_settings):
    new_recipes = {"data": [{"experiment1": True}, {"experiment2": False}]}
    remote_settings.update_recipes(new_recipes)
    assert remote_settings.get_recipes() == new_recipes


@patch("cirrus.experiment_recipes.requests.get")
@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_empty_data_key(mock_get, remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"changes": []}
    mock_get.return_value = mock_response

    remote_settings.fetch_recipes()
    assert remote_settings.get_recipes() == {"data": []}


@patch("cirrus.experiment_recipes.requests.get")
@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_non_empty_data_key(mock_get, remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "changes": [{"experiment1": True}, {"experiment2": False}]
    }
    mock_get.return_value = mock_response

    remote_settings.fetch_recipes()
    assert remote_settings.get_recipes() == {
        "data": [{"experiment1": True}, {"experiment2": False}]
    }


@patch("cirrus.experiment_recipes.requests.get")
@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_successful_response(mock_get, remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"changes": []}
    mock_get.return_value = mock_response

    remote_settings.fetch_recipes()
    assert mock_get.call_count == 1
    mock_get.assert_any_call(remote_settings.url)


@patch("cirrus.experiment_recipes.requests.get")
@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_failed_request(mock_get, remote_settings):
    mock_get.side_effect = requests.exceptions.RequestException("Failed request")

    with pytest.raises(requests.exceptions.RequestException) as context:
        remote_settings.fetch_recipes()

    assert str(context.value) == "Failed request"
    assert remote_settings.get_recipes() == {"data": []}


@patch("cirrus.experiment_recipes.requests.get")
@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_empty_data_key_with_non_empty_recipes(mock_get, remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"changes": []}
    mock_get.return_value = mock_response

    remote_settings.update_recipes({"data": [{"experiment1": True}]})
    remote_settings.fetch_recipes()
    assert remote_settings.get_recipes() == {"data": []}


@patch("cirrus.experiment_recipes.requests.get")
@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_non_data_key_recipes(mock_get, remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_get.return_value = mock_response

    remote_settings.fetch_recipes()
    assert remote_settings.get_recipes() == {"data": []}


@pytest.mark.parametrize(
    "slug, expected_type",
    [
        ("cirrus-test-1", RecipeType.ROLLOUT.value),
        ("cirrus-test-2", RecipeType.EXPERIMENT.value),
        ("non-existent-slug", RecipeType.EMPTY.value),
    ],
)
@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_get_recipe_type_with_actual_recipes(
    remote_settings, recipes, slug, expected_type
):
    remote_settings.update_recipes(recipes)
    experiment_type = remote_settings.get_recipe_type(slug)
    assert experiment_type == expected_type
