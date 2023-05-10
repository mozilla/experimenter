import pytest

from ..cirrus.main import fetch_schedule_recipes, remote_setting_refresh_rate_in_seconds


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


def test_get_features(client):
    response = client.get("/v1/features/")
    assert response.status_code == 200
    assert response.json() == {"feature": "test"}


@pytest.mark.asyncio
async def test_fetch_schedule_recipes_success(scheduler_mock, remote_setting_mock):
    # Arrange
    # Set up the remote_setting_mock to return a value
    remote_setting_mock.fetch_recipes.return_value = ["recipe1", "recipe2"]

    # Act
    await fetch_schedule_recipes()

    # Assert
    # Check that the remote_setting_mock.fetch_recipes method was called
    remote_setting_mock.fetch_recipes.assert_called_once()

    # Check that no jobs were added to the scheduler
    scheduler_mock.add_job.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_schedule_recipes_failure(
    scheduler_mock, remote_setting_mock, exception
):
    # Arrange
    # Set up the remote_setting_mock to raise an exception
    remote_setting_mock.fetch_recipes.side_effect = exception

    # Act
    await fetch_schedule_recipes()

    # Assert
    # Check that the remote_setting_mock.fetch_recipes method was called
    remote_setting_mock.fetch_recipes.assert_called_once()

    # Check that a job was added to the scheduler to retry after 10 seconds
    scheduler_mock.add_job.assert_called_once_with(
        fetch_schedule_recipes,
        "interval",
        seconds=remote_setting_refresh_rate_in_seconds,
        max_instances=1,
        max_retries=3,
    )


@pytest.mark.asyncio
async def test_fetch_schedule_recipes_retry(
    scheduler_mock, remote_setting_mock, exception
):
    # Arrange
    # Set up the remote_setting_mock to raise an exception the first time it is called,
    # and return a value the second time it is called
    remote_setting_mock.fetch_recipes.side_effect = [exception, ["recipe1", "recipe2"]]

    # Act
    await fetch_schedule_recipes()

    # Check that a job was added to the scheduler to retry after 10 seconds
    scheduler_mock.add_job.assert_called_once_with(
        fetch_schedule_recipes,
        "interval",
        seconds=remote_setting_refresh_rate_in_seconds,
        max_instances=1,
        max_retries=3,
    )
