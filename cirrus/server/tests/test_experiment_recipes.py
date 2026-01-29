from unittest.mock import MagicMock, patch

import pytest
import responses
from requests.exceptions import RequestException
from responses.registries import OrderedRegistry
from urllib3.util import Retry

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


@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_empty_data_key(remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"changes": []}

    with patch.object(remote_settings.session, "get") as mock_get:
        mock_get.return_value = mock_response
        remote_settings.fetch_recipes()

    assert remote_settings.get_recipes() == {"data": []}


@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_non_empty_data_key(remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "changes": [{"experiment1": True}, {"experiment2": False}]
    }
    with patch.object(remote_settings.session, "get") as mock_get:
        mock_get.return_value = mock_response
        remote_settings.fetch_recipes()

    assert remote_settings.get_recipes() == {
        "data": [{"experiment1": True}, {"experiment2": False}]
    }


@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_successful_response(remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"changes": []}

    with patch.object(remote_settings.session, "get") as mock_get:
        mock_get.return_value = mock_response
        remote_settings.fetch_recipes()

    assert mock_get.call_count == 1
    mock_get.assert_any_call(remote_settings.url)


@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_failed_request(remote_settings):
    with (
        patch.object(remote_settings.session, "get") as mock_get,
        pytest.raises(RequestException) as context,
    ):
        mock_get.side_effect = RequestException("Failed request")
        remote_settings.fetch_recipes()

    assert str(context.value) == "Failed request"
    assert remote_settings.get_recipes() == {"data": []}


@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_empty_data_key_with_non_empty_recipes(remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"changes": []}

    remote_settings.update_recipes({"data": [{"experiment1": True}]})

    with patch.object(remote_settings.session, "get") as mock_get:
        mock_get.return_value = mock_response
        remote_settings.fetch_recipes()

    assert remote_settings.get_recipes() == {"data": []}


@pytest.mark.parametrize(
    "remote_settings",
    ["remote_settings_live", "remote_settings_preview"],
    indirect=True,
)
def test_non_data_key_recipes(remote_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}

    with patch.object(remote_settings.session, "get") as mock_get:
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


@responses.activate
@pytest.mark.parametrize("protocol", ["http", "https"])
def test_fetch_recipes_with_retry_failure(sdk_live, protocol):
    url = f"{protocol}://example.com/changeset?_expected=0"
    response = responses.get(url, json={}, status=500)
    retry = Retry(
        total=2,
        backoff_factor=0.01,
        status_forcelist=[500],
    )
    rs = RemoteSettings(url, sdk_live, retry)
    with pytest.raises(RequestException):
        rs.fetch_recipes()
    assert response.call_count == 3


@responses.activate(registry=OrderedRegistry)
@pytest.mark.parametrize("protocol", ["http", "https"])
def test_fetch_recipes_with_retry_success(sdk_live, protocol):
    url = f"{protocol}://example.com/changeset?_expected=0"
    _responses = [
        responses.get(url, json={}, status=500),
        responses.get(url, json={}, status=500),
        responses.get(url, json={"changes": []}, status=200),
    ]
    retry = Retry(
        total=2,
        backoff_factor=0.01,
        status_forcelist=[500],
    )
    rs = RemoteSettings(url, sdk_live, retry)
    rs.fetch_recipes()
    assert [r.call_count for r in _responses] == [1, 1, 1]
