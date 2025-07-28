import logging
import sys
from unittest.mock import patch

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cirrus_sdk import NimbusError
from fastapi import status
from fml_sdk import FmlError

from cirrus.main import (
    EnrollmentMetricData,
    create_fml,
    create_scheduler,
    create_sdk,
    fetch_schedule_recipes,
    verify_settings,
)


def test_create_fml_with_error():
    with patch.object(sys, "exit") as mock_exit, patch("cirrus.main.FML") as mock_fml:
        mock_fml.side_effect = FmlError("Error occurred during FML creation")

        fml = create_fml()

        mock_exit.assert_called_once_with(1)  # Assert that sys.exit(1) was called
        assert fml is None


def test_create_sdk_with_error(metrics_handler):
    with patch.object(sys, "exit") as mock_exit, patch("cirrus.main.SDK") as mock_sdk:
        mock_sdk.side_effect = NimbusError("Error occurred during SDK creation")

        sdk = create_sdk([], metrics_handler)

        mock_exit.assert_called_once_with(1)  # Assert that sys.exit(1) was called
        assert sdk is None


def test_create_scheduler():
    scheduler = create_scheduler()

    assert isinstance(scheduler, AsyncIOScheduler)


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


def test_get_features_v1_with_required_field(client):
    request_data = {
        "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
        "context": {
            "key1": "value1",
            "key2": {"key2.1": "value2", "key2.2": "value3"},
        },
    }

    response = client.post("/v1/features/", json=request_data)
    assert response.status_code == 200
    assert response.json() == {
        "example-feature": {"enabled": False, "something": "wicked"}
    }


def test_get_features_v2_with_required_field(client):
    request_data = {
        "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
        "context": {
            "key1": "value1",
            "key2": {"key2.1": "value2", "key2.2": "value3"},
        },
    }

    response = client.post("/v2/features/", json=request_data)
    assert response.status_code == 200
    assert response.json() == {
        "Features": {
            "example-feature": {"enabled": False, "something": "wicked"},
            # return default features
        },
        "Enrollments": [],
    }


@pytest.mark.parametrize(
    "request_data, expected_status, expected_message",
    [
        pytest.param(
            {
                "client_id": "",
                "context": {
                    "key1": "value1",
                    "key2": {"key2.1": "value2", "key2.2": "value3"},
                },
            },
            status.HTTP_400_BAD_REQUEST,
            "Client ID value is missing or empty",
            id="empty_client_id",
        ),
        pytest.param(
            {
                "context": {
                    "key1": "value1",
                    "key2": {"key2.1": "value2", "key2.2": "value3"},
                }
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "missing",
                    "loc": ["body", "client_id"],
                    "msg": "Field required",
                    "input": {
                        "context": {
                            "key1": "value1",
                            "key2": {"key2.1": "value2", "key2.2": "value3"},
                        }
                    },
                }
            ],
            id="missing_client_id",
        ),
        pytest.param(
            {"client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449"},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "missing",
                    "loc": ["body", "context"],
                    "msg": "Field required",
                    "input": {"client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449"},
                }
            ],
            id="missing_client_id_and_context",
        ),
        pytest.param(
            {},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "missing",
                    "loc": ["body", "client_id"],
                    "msg": "Field required",
                    "input": {},
                },
                {
                    "type": "missing",
                    "loc": ["body", "context"],
                    "msg": "Field required",
                    "input": {},
                },
            ],
            id="missing_context",
        ),
    ],
)
def test_get_features_v1_missing_required_field(
    client, request_data, expected_status, expected_message
):
    response = client.post("/v1/features/", json=request_data)
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_message


@pytest.mark.parametrize(
    "request_data, expected_status, expected_message",
    [
        pytest.param(
            {
                "client_id": "",
                "context": {
                    "key1": "value1",
                    "key2": {"key2.1": "value2", "key2.2": "value3"},
                },
            },
            status.HTTP_400_BAD_REQUEST,
            "Client ID value is missing or empty",
            id="empty_client_id",
        ),
        pytest.param(
            {
                "context": {
                    "key1": "value1",
                    "key2": {"key2.1": "value2", "key2.2": "value3"},
                }
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "missing",
                    "loc": ["body", "client_id"],
                    "msg": "Field required",
                    "input": {
                        "context": {
                            "key1": "value1",
                            "key2": {"key2.1": "value2", "key2.2": "value3"},
                        }
                    },
                }
            ],
            id="missing_client_id",
        ),
        pytest.param(
            {"client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449"},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "missing",
                    "loc": ["body", "context"],
                    "msg": "Field required",
                    "input": {"client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449"},
                }
            ],
            id="missing_context",
        ),
        pytest.param(
            {},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "missing",
                    "loc": ["body", "client_id"],
                    "msg": "Field required",
                    "input": {},
                },
                {
                    "type": "missing",
                    "loc": ["body", "context"],
                    "msg": "Field required",
                    "input": {},
                },
            ],
            id="missing_client_id_and_context",
        ),
    ],
)
def test_get_features_v2_missing_required_field(
    client, request_data, expected_status, expected_message
):
    response = client.post("/v2/features/", json=request_data)
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_message


@pytest.mark.asyncio
@patch("cirrus.main.app.state.remote_setting_live")
@patch("cirrus.main.app.state.remote_setting_preview")
async def test_fetch_schedule_recipes_success(
    mock_remote_setting_live, mock_remote_setting_preview, scheduler_mock
):
    mock_remote_setting_live.fetch_recipes.return_value = {
        "data": [{"experiment1": True}, {"experiment2": False}]
    }
    mock_remote_setting_preview.fetch_recipes.return_value = {
        "data": [{"experiment1": True}, {"experiment2": False}]
    }

    await fetch_schedule_recipes()
    mock_remote_setting_live.fetch_recipes.assert_called_once()
    mock_remote_setting_preview.fetch_recipes.assert_called_once()

    # Check that no jobs were added to the scheduler
    scheduler_mock.add_job.assert_not_called()


@pytest.mark.asyncio
@patch("cirrus.main.app.state.scheduler")
@patch("cirrus.main.app.state.remote_setting_live")
async def test_fetch_schedule_recipes_failure_live(
    mock_remote_setting_live, scheduler_mock
):
    mock_remote_setting_live.fetch_recipes.side_effect = Exception("some error")

    await fetch_schedule_recipes()

    mock_remote_setting_live.fetch_recipes.assert_called_once()

    # Check that a job was added to the scheduler to retry after 30 seconds
    scheduler_mock.add_job.assert_called_once_with(
        fetch_schedule_recipes,
        "interval",
        seconds=30,
        max_instances=1,
        max_retries=3,
    )


@pytest.mark.asyncio
@patch("cirrus.main.app.state.scheduler")
@patch("cirrus.main.app.state.remote_setting_preview")
async def test_fetch_schedule_recipes_failure_preview(
    mock_remote_setting_preview, scheduler_mock
):
    mock_remote_setting_preview.fetch_recipes.side_effect = Exception("some error")

    await fetch_schedule_recipes()

    mock_remote_setting_preview.fetch_recipes.assert_called_once()

    # Check that a job was added to the scheduler to retry after 30 seconds
    scheduler_mock.add_job.assert_called_once_with(
        fetch_schedule_recipes,
        "interval",
        seconds=30,
        max_instances=1,
        max_retries=3,
    )


@pytest.mark.asyncio
@patch("cirrus.main.app.state.scheduler")
@patch("cirrus.main.app.state.remote_setting_live")
@patch("cirrus.main.app.state.remote_setting_preview")
async def test_fetch_schedule_recipes_both_fail(
    mock_remote_setting_live, mock_remote_setting_preview, scheduler_mock
):
    mock_remote_setting_live.fetch_recipes.side_effect = Exception("live error")
    mock_remote_setting_preview.fetch_recipes.side_effect = Exception("preview error")

    await fetch_schedule_recipes()

    mock_remote_setting_live.fetch_recipes.assert_called_once()
    mock_remote_setting_preview.fetch_recipes.assert_called_once()

    # Check that only one job was added to the scheduler to retry after 30 seconds
    scheduler_mock.add_job.assert_called_once_with(
        fetch_schedule_recipes,
        "interval",
        seconds=30,
        max_instances=1,
        max_retries=3,
    )


@pytest.mark.asyncio
@patch("cirrus.main.app.state.scheduler")
@patch("cirrus.main.app.state.remote_setting_live")
@patch("cirrus.main.app.state.remote_setting_preview")
async def test_fetch_schedule_recipes_live_fails_preview_succeeds(
    mock_remote_setting_live, mock_remote_setting_preview, scheduler_mock
):
    mock_remote_setting_live.fetch_recipes.side_effect = Exception("live error")
    mock_remote_setting_preview.fetch_recipes.return_value = {
        "data": [{"experiment1": True}, {"experiment2": False}]
    }

    await fetch_schedule_recipes()

    mock_remote_setting_live.fetch_recipes.assert_called_once()
    mock_remote_setting_preview.fetch_recipes.assert_called_once()

    # Check that a job was added to the scheduler to retry after 30 seconds
    scheduler_mock.add_job.assert_called_once_with(
        fetch_schedule_recipes,
        "interval",
        seconds=30,
        max_instances=1,
        max_retries=3,
    )


@pytest.mark.asyncio
@patch("cirrus.main.app.state.scheduler")
@patch("cirrus.main.app.state.remote_setting_live")
@patch("cirrus.main.app.state.remote_setting_preview")
async def test_fetch_schedule_recipes_preview_fails_live_succeeds(
    mock_remote_setting_live, mock_remote_setting_preview, scheduler_mock
):
    mock_remote_setting_live.fetch_recipes.return_value = {
        "data": [{"experiment1": True}, {"experiment2": False}]
    }
    mock_remote_setting_preview.fetch_recipes.side_effect = Exception("preview error")

    await fetch_schedule_recipes()

    mock_remote_setting_live.fetch_recipes.assert_called_once()
    mock_remote_setting_preview.fetch_recipes.assert_called_once()

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
    scheduler_mock, remote_setting_live_mock, exception
):
    # Set up the remote_setting_mock to raise an exception the first time it is called
    # and return a value the second time it is called
    remote_setting_live_mock.fetch_recipes.side_effect = [
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


def test_lbheartbeat_endpoint(client):
    response = client.get("/__lbheartbeat__")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_heartbeat_endpoint(client):
    response = client.get("/__heartbeat__")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "context",
    [
        pytest.param({}, id="empty_context"),
        pytest.param(
            {
                "key1": "value1",
                "key2": {"key2.1": "value2", "key2.2": "value3"},
            },
            id="nonempty_context",
        ),
    ],
)
def test_get_features_v1_with_nimbus_preview_flag(client, context):
    request_data = {
        "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
        "context": context,
    }

    response = client.post("/v1/features/?nimbus_preview=true", json=request_data)
    assert response.status_code == 200
    assert response.json() == {
        "example-feature": {"enabled": False, "something": "wicked"}
    }


@pytest.mark.parametrize(
    "context",
    [
        pytest.param({}, id="empty_context"),
        pytest.param(
            {
                "key1": "value1",
                "key2": {"key2.1": "value2", "key2.2": "value3"},
            },
            id="nonempty_context",
        ),
    ],
)
def test_get_features_v2_with_nimbus_preview(client, context):
    request_data = {
        "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
        "context": context,
    }

    response = client.post("/v2/features/?nimbus_preview=true", json=request_data)
    assert response.status_code == 200
    assert response.json() == {
        "Features": {
            "example-feature": {"enabled": False, "something": "wicked"},
            # return default features
        },
        "Enrollments": [],
    }


@pytest.mark.parametrize(
    "request_data, expected_status, expected_message",
    [
        pytest.param(
            {
                "client_id": "",
                "context": {
                    "key1": "value1",
                    "key2": {"key2.1": "value2", "key2.2": "value3"},
                },
            },
            status.HTTP_400_BAD_REQUEST,
            "Client ID value is missing or empty",
            id="empty_client_id",
        ),
        pytest.param(
            {
                "context": {
                    "key1": "value1",
                    "key2": {"key2.1": "value2", "key2.2": "value3"},
                }
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "missing",
                    "loc": ["body", "client_id"],
                    "msg": "Field required",
                    "input": {
                        "context": {
                            "key1": "value1",
                            "key2": {"key2.1": "value2", "key2.2": "value3"},
                        }
                    },
                }
            ],
            id="missing_client_id",
        ),
        pytest.param(
            {"client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449"},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "missing",
                    "loc": ["body", "context"],
                    "msg": "Field required",
                    "input": {"client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449"},
                }
            ],
            id="missing_context",
        ),
        pytest.param(
            {},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "missing",
                    "loc": ["body", "client_id"],
                    "msg": "Field required",
                    "input": {},
                },
                {
                    "type": "missing",
                    "loc": ["body", "context"],
                    "msg": "Field required",
                    "input": {},
                },
            ],
            id="missing_client_id_and_context",
        ),
    ],
)
def test_get_features_v1_missing_required_field_nimbus_preview(
    client, request_data, expected_status, expected_message
):
    response = client.post("/v1/features/?nimbus_preview=true", json=request_data)
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_message


@pytest.mark.parametrize(
    "request_data, expected_status, expected_message",
    [
        pytest.param(
            {
                "client_id": "",
                "context": {
                    "key1": "value1",
                    "key2": {"key2.1": "value2", "key2.2": "value3"},
                },
            },
            status.HTTP_400_BAD_REQUEST,
            "Client ID value is missing or empty",
            id="empty_client_id",
        ),
        pytest.param(
            {
                "context": {
                    "key1": "value1",
                    "key2": {"key2.1": "value2", "key2.2": "value3"},
                }
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "missing",
                    "loc": ["body", "client_id"],
                    "msg": "Field required",
                    "input": {
                        "context": {
                            "key1": "value1",
                            "key2": {"key2.1": "value2", "key2.2": "value3"},
                        }
                    },
                }
            ],
            id="missing_client_id",
        ),
        pytest.param(
            {"client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449"},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "missing",
                    "loc": ["body", "context"],
                    "msg": "Field required",
                    "input": {"client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449"},
                }
            ],
            id="missing_context",
        ),
        pytest.param(
            {},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            [
                {
                    "type": "missing",
                    "loc": ["body", "client_id"],
                    "msg": "Field required",
                    "input": {},
                },
                {
                    "type": "missing",
                    "loc": ["body", "context"],
                    "msg": "Field required",
                    "input": {},
                },
            ],
            id="missing_client_id_and_context",
        ),
    ],
)
def test_get_features_v2_missing_required_field_nimbus_preview(
    client, request_data, expected_status, expected_message
):
    response = client.post("/v2/features/?nimbus_preview=true", json=request_data)
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_message


@pytest.mark.parametrize(
    "context",
    [
        pytest.param({}, id="empty_context"),
        pytest.param(
            {
                "key1": "value1",
                "key2": {"key2.1": "value2", "key2.2": "value3"},
            },
            id="nonempty_context",
        ),
    ],
)
def test_get_features_v1_without_nimbus_preview(client, context):
    request_data = {
        "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
        "context": context,
    }

    with patch(
        "cirrus.main.app.state.sdk_live.compute_enrollments"
    ) as mock_sdk_live_compute_enrollments:

        mock_sdk_live_compute_enrollments.return_value = {
            "enrolledFeatureConfigMap": {
                "example-feature": {
                    "feature": {
                        "featureId": "example-feature",
                        "value": {"enabled": False, "something": "wicked"},
                    },
                    "branch": "treatment",
                    "featureId": "example-feature",
                    "slug": "experiment_slug_1",
                }
            },
            "enrollments": [
                {
                    "slug": "experiment_slug_1",
                    "status": {
                        "Enrolled": {
                            "branch": "treatment",
                            "enrollment_id": "enrollment_id_1",
                            "reason": "Qualified",
                        }
                    },
                }
            ],
            "events": [
                {
                    "branch_slug": "treatment",
                    "change": "Enrollment",
                    "enrollment_id": "enrollment_id_1",
                    "experiment_slug": "experiment_slug_1",
                    "reason": None,
                }
            ],
        }

        # Without nimbus_preview
        response = client.post("/v1/features/", json=request_data)
        assert response.status_code == 200
        assert response.json() == {
            "example-feature": {"enabled": False, "something": "wicked"}
        }


@pytest.mark.parametrize(
    "context",
    [
        pytest.param({}, id="empty_context"),
        pytest.param(
            {
                "key1": "value1",
                "key2": {"key2.1": "value2", "key2.2": "value3"},
            },
            id="nonempty_context",
        ),
    ],
)
def test_get_features_v1_with_nimbus_preview(client, context):
    request_data = {
        "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
        "context": context,
    }

    with patch(
        "cirrus.main.app.state.sdk_preview.compute_enrollments"
    ) as mock_sdk_preview_compute_enrollments:

        mock_sdk_preview_compute_enrollments.return_value = {
            "enrolledFeatureConfigMap": {
                "example-feature": {
                    "feature": {
                        "featureId": "example-feature",
                        "value": {"enabled": True, "something": "preview"},
                    },
                    "branch": "treatment",
                    "featureId": "example-feature",
                    "slug": "experiment_slug_2",
                }
            },
            "enrollments": [
                {
                    "slug": "experiment_slug_2",
                    "status": {
                        "Enrolled": {
                            "branch": "treatment",
                            "enrollment_id": "enrollment_id_2",
                            "reason": "Qualified",
                        }
                    },
                }
            ],
            "events": [
                {
                    "branch_slug": "treatment",
                    "change": "Enrollment",
                    "enrollment_id": "enrollment_id_2",
                    "experiment_slug": "experiment_slug_2",
                    "reason": None,
                }
            ],
        }

        # With nimbus_preview
        response = client.post("/v1/features/?nimbus_preview=true", json=request_data)
        assert response.status_code == 200
        assert response.json() == {
            "example-feature": {"enabled": True, "something": "preview"}
        }


def test_get_features_v2_enrollments_without_nimbus_preview(client):
    request_data = {
        "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
        "context": {
            "key1": "value1",
            "key2": {"key2.1": "value2", "key2.2": "value3"},
        },
    }

    with patch(
        "cirrus.main.app.state.sdk_live.compute_enrollments"
    ) as mock_sdk_live_compute_enrollments, patch(
        "cirrus.main.collate_enrollment_metric_data"
    ) as mock_collate_enrollment_metric_data, patch(
        "cirrus.main.app.state.fml.compute_feature_configurations"
    ) as mock_compute_feature_configurations:

        # Mock live compute_enrollments response
        mock_sdk_live_compute_enrollments.return_value = {
            "enrolledFeatureConfigMap": {
                "example-feature": {
                    "feature": {
                        "featureId": "example-feature",
                        "value": {"enabled": False, "something": "wicked"},
                    },
                    "branch": "treatment",
                    "featureId": "example-feature",
                    "slug": "experiment_slug_1",
                }
            },
            "enrollments": [
                {
                    "slug": "experiment_slug_1",
                    "status": {
                        "Enrolled": {
                            "branch": "treatment",
                            "enrollment_id": "enrollment_id_1",
                            "reason": "Qualified",
                        }
                    },
                }
            ],
            "events": [
                {
                    "branch_slug": "treatment",
                    "change": "Enrollment",
                    "enrollment_id": "enrollment_id_1",
                    "experiment_slug": "experiment_slug_1",
                    "reason": None,
                }
            ],
        }

        # Mock collate_enrollment_metric_data and compute_feature_configurations
        mock_collate_enrollment_metric_data.side_effect = (
            lambda enrolled_partial_configuration, client_id, nimbus_preview_flag: [
                EnrollmentMetricData(
                    nimbus_user_id=client_id,
                    app_id="test_app_id",
                    experiment_slug=event["experiment_slug"],
                    branch_slug=event["branch_slug"],
                    experiment_type="rollout",
                    is_preview=nimbus_preview_flag,
                )
                for event in enrolled_partial_configuration["events"]
            ]
        )
        mock_compute_feature_configurations.side_effect = (
            lambda enrolled_partial_configuration: {
                feature_id: feature_data["feature"]["value"]
                for feature_id, feature_data in enrolled_partial_configuration[
                    "enrolledFeatureConfigMap"
                ].items()
            }
        )

        # Test for live SDK (no nimbus_preview)
        response = client.post("/v2/features/", json=request_data)
        assert response.status_code == 200
        assert response.json() == {
            "Features": {
                "example-feature": {"enabled": False, "something": "wicked"},
            },
            "Enrollments": [
                {
                    "nimbus_user_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
                    "app_id": "test_app_id",
                    "experiment": "experiment_slug_1",
                    "branch": "treatment",
                    "experiment_type": "rollout",
                    "is_preview": False,
                }
            ],
        }


def test_get_features_v2_enrollments_with_nimbus_preview(client):
    request_data = {
        "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
        "context": {
            "key1": "value1",
            "key2": {"key2.1": "value2", "key2.2": "value3"},
        },
    }

    with patch(
        "cirrus.main.app.state.sdk_preview.compute_enrollments"
    ) as mock_sdk_preview_compute_enrollments, patch(
        "cirrus.main.collate_enrollment_metric_data"
    ) as mock_collate_enrollment_metric_data, patch(
        "cirrus.main.app.state.fml.compute_feature_configurations"
    ) as mock_compute_feature_configurations:

        # Mock preview compute_enrollments response
        mock_sdk_preview_compute_enrollments.return_value = {
            "enrolledFeatureConfigMap": {
                "example-feature": {
                    "feature": {
                        "featureId": "example-feature",
                        "value": {"enabled": True, "something": "preview"},
                    },
                    "branch": "treatment",
                    "featureId": "example-feature",
                    "slug": "experiment_slug_2",
                }
            },
            "enrollments": [
                {
                    "slug": "experiment_slug_2",
                    "status": {
                        "Enrolled": {
                            "branch": "treatment",
                            "enrollment_id": "enrollment_id_2",
                            "reason": "Qualified",
                        }
                    },
                }
            ],
            "events": [
                {
                    "branch_slug": "treatment",
                    "change": "Enrollment",
                    "enrollment_id": "enrollment_id_2",
                    "experiment_slug": "experiment_slug_2",
                    "reason": None,
                }
            ],
        }

        # Mock collate_enrollment_metric_data and compute_feature_configurations
        mock_collate_enrollment_metric_data.side_effect = (
            lambda enrolled_partial_configuration, client_id, nimbus_preview_flag: [
                EnrollmentMetricData(
                    nimbus_user_id=client_id,
                    app_id="test_app_id",
                    experiment_slug=event["experiment_slug"],
                    branch_slug=event["branch_slug"],
                    experiment_type="experiment",
                    is_preview=nimbus_preview_flag,
                )
                for event in enrolled_partial_configuration["events"]
            ]
        )
        mock_compute_feature_configurations.side_effect = (
            lambda enrolled_partial_configuration: {
                feature_id: feature_data["feature"]["value"]
                for feature_id, feature_data in enrolled_partial_configuration[
                    "enrolledFeatureConfigMap"
                ].items()
            }
        )

        # Test for preview SDK (nimbus_preview=true)
        response = client.post("/v2/features/?nimbus_preview=true", json=request_data)
        assert response.status_code == 200
        assert response.json() == {
            "Features": {
                "example-feature": {"enabled": True, "something": "preview"},
            },
            "Enrollments": [
                {
                    "nimbus_user_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
                    "app_id": "test_app_id",
                    "experiment": "experiment_slug_2",
                    "branch": "treatment",
                    "experiment_type": "experiment",
                    "is_preview": True,
                }
            ],
        }


def test_get_features_v1_preview_url_not_provided(client):
    request_data = {
        "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
        "context": {
            "key1": "value1",
            "key2": {"key2.1": "value2", "key2.2": "value3"},
        },
    }

    # Assuming the remote_setting_preview_url is not set in the settings
    with patch("cirrus.main.remote_setting_preview_url", ""):
        response = client.post("/v1/features/?nimbus_preview=true", json=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "This Cirrus doesn’t support preview mode"}


def test_get_features_v2_preview_url_not_provided(client):
    request_data = {
        "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
        "context": {
            "key1": "value1",
            "key2": {"key2.1": "value2", "key2.2": "value3"},
        },
    }

    # Assuming the remote_setting_preview_url is not set in the settings
    with patch("cirrus.main.remote_setting_preview_url", ""):
        response = client.post("/v2/features/?nimbus_preview=true", json=request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "This Cirrus doesn’t support preview mode"}


def test_verify_settings_logs_error_and_exits(caplog):
    with patch("cirrus.main.remote_setting_url", ""), patch.object(
        sys, "exit", side_effect=SystemExit
    ) as mock_exit, caplog.at_level(logging.ERROR):
        with pytest.raises(SystemExit):
            verify_settings()

        mock_exit.assert_called_once_with(1)
        assert "Remote setting URL is required but not provided." in caplog.text
