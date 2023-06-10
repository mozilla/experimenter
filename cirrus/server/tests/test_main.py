import pytest

from cirrus.main import fetch_schedule_recipes


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


def test_get_features(client):
    response = client.post("/v1/features/")
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
    # Set up the remote_setting_mock to raise an exception the first time it is called,
    # and return a value the second time it is called
    remote_setting_mock.fetch_recipes.side_effect = [exception, ["recipe1", "recipe2"]]

    await fetch_schedule_recipes()

    # Check that a job was added to the scheduler to retry after 30 seconds
    scheduler_mock.add_job.assert_called_once_with(
        fetch_schedule_recipes,
        "interval",
        seconds=30,
        max_instances=1,
        max_retries=3,
    )
