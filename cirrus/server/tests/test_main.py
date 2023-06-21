import sys
from unittest.mock import patch

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cirrus_sdk import NimbusError
from fml_sdk import FmlError

from cirrus.main import (
    create_fml,
    create_scheduler,
    create_sdk,
    fetch_schedule_recipes,
)


def test_create_fml_with_error():
    with patch.object(sys, "exit") as mock_exit, patch("cirrus.main.FML") as mock_fml:
        mock_fml.side_effect = FmlError("Error occurred during FML creation")

        fml = create_fml()

        mock_exit.assert_called_once_with(1)  # Assert that sys.exit(1) was called
        assert fml is None


def test_create_sdk_with_error():
    with patch.object(sys, "exit") as mock_exit, patch("cirrus.main.SDK") as mock_sdk:
        mock_sdk.side_effect = NimbusError("Error occurred during SDK creation")

        sdk = create_sdk()

        mock_exit.assert_called_once_with(1)  # Assert that sys.exit(1) was called
        assert sdk is None


def test_create_scheduler():
    scheduler = create_scheduler()

    assert isinstance(scheduler, AsyncIOScheduler)


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


@pytest.mark.parametrize(
    "request_data",
    [
        {
            "client_id": "",  # client id value is missing
            "context": {
                "key1": "value1",
                "key2": {"key2.1": "value2", "key2.2": "value3"},
            },
        },
        {
            # client id is missing
            "context": {
                "key1": "value1",
                "key2": {"key2.1": "value2", "key2.2": "value3"},
            },
        },
        {
            "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
            "context": {},  # context value is missing
        },
        {
            "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
            # context key is missing
        },
        {  # clinet id key is missing
            # context key is missing
        },
    ],
)
def test_get_features_returns_default(client, request_data):
    response = client.post("/v1/features/", json=request_data)
    assert response.status_code == 200
    assert response.json() == {
        "example-feature": {"enabled": False, "something": "wicked"}
    }


@pytest.mark.asyncio
async def test_fetch_schedule_recipes_success(scheduler_mock, remote_setting_mock):
    remote_setting_mock.fetch_recipes.return_value = {
        "data": [{"experiment1": True}, {"experiment2": False}]
    }

    await fetch_schedule_recipes()
    remote_setting_mock.fetch_recipes.assert_called_once()

    # Check that no jobs were added to the scheduler
    scheduler_mock.add_job.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_schedule_recipes_failure(
    scheduler_mock, remote_setting_mock, exception
):
    remote_setting_mock.fetch_recipes.side_effect = exception

    await fetch_schedule_recipes()

    remote_setting_mock.fetch_recipes.assert_called_once()

    # Check that a job was added to the scheduler to retry after 30 seconds
    scheduler_mock.add_job.assert_called_once_with(
        fetch_schedule_recipes,
        "interval",
        seconds=30,
        max_instances=1,
        max_retries=3,
    )


@pytest.mark.asyncio
async def test_fetch_schedule_recipes_retry(
    scheduler_mock, remote_setting_mock, exception
):
    # Set up the remote_setting_mock to raise an exception the first time it is called
    # and return a value the second time it is called
    remote_setting_mock.fetch_recipes.side_effect = [
        exception,
        ["recipe1", "recipe2"],
    ]

    await fetch_schedule_recipes()

    # Check that a job was added to the scheduler to retry after 30 seconds
    scheduler_mock.add_job.assert_called_once_with(
        fetch_schedule_recipes,
        "interval",
        seconds=30,
        max_instances=1,
        max_retries=3,
    )
