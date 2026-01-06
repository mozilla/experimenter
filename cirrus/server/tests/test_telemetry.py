import json

import pytest

from cirrus.experiment_recipes import RecipeType
from cirrus.main import (
    EnrollmentMetricData,
    app,
    collate_enrollment_metric_data,
    record_metrics,
    send_instance_name_metric,
)
from cirrus.sdk import SDK, CirrusMetricsHandler


@pytest.mark.asyncio
async def test_enrollment_metrics_recorded_with_record_metrics(mocker, recipes):
    app.state.remote_setting_live.update_recipes(recipes)
    record_mock = mocker.patch.object(app.state.enrollment_ping, "record")

    # Create the enrollment data
    enrollment_data = [
        EnrollmentMetricData(
            nimbus_user_id="test_client_id",
            app_id="test_app_id",
            experiment_slug="cirrus-test-1",
            branch_slug="control",
            experiment_type=RecipeType.ROLLOUT.value,
            is_preview=False,
        ),
        EnrollmentMetricData(
            nimbus_user_id="test_client_id",
            app_id="test_app_id",
            experiment_slug="cirrus-test-2",
            branch_slug="control",
            experiment_type=RecipeType.EXPERIMENT.value,
            is_preview=False,
        ),
    ]

    await record_metrics(enrollment_data, "test_client_id")

    record_mock.assert_called_once_with(
        user_agent=None,
        ip_address=None,
        nimbus_nimbus_user_id="test_client_id",
        events=[
            {
                "category": "cirrus_events",
                "name": "enrollment_status",
                "extra": {
                    "nimbus_user_id": "test_client_id",
                    "app_id": "test_app_id",
                    "experiment": "cirrus-test-1",
                    "branch": "control",
                    "experiment_type": RecipeType.ROLLOUT.value,
                    "is_preview": "false",
                },
            },
            {
                "category": "cirrus_events",
                "name": "enrollment_status",
                "extra": {
                    "nimbus_user_id": "test_client_id",
                    "app_id": "test_app_id",
                    "experiment": "cirrus-test-2",
                    "branch": "control",
                    "experiment_type": RecipeType.EXPERIMENT.value,
                    "is_preview": "false",
                },
            },
        ],
    )


def test_collate_enrollment_metric_data(mocker):
    mock_remote_settings = mocker.patch("cirrus.main.app.state.remote_setting_live")
    mock_remote_settings.get_recipe_type.return_value = "rollout"

    enrolled_partial_configuration = {
        "enrolledFeatureConfigMap": {
            "example-feature": {
                "branch": None,
                "feature": {
                    "featureId": "example-feature",
                    "value": {"enabled": False, "something": "You are enrolled"},
                },
                "featureId": "example-feature",
                "slug": "experiment-slug",
            }
        },
        "enrollments": [
            {
                "slug": "experiment-slug",
                "status": {"Enrolled": {"branch": "control", "reason": "Qualified"}},
            }
        ],
        "events": [
            {
                "branch_slug": "control",
                "change": "Enrollment",
                "experiment_slug": "experiment-slug",
                "reason": None,
            }
        ],
    }
    result = collate_enrollment_metric_data(
        enrolled_partial_configuration, "test-client-id", nimbus_preview_flag=False
    )
    expected_result = [
        EnrollmentMetricData(
            nimbus_user_id="test-client-id",
            app_id="test_app_id",
            experiment_slug="experiment-slug",
            branch_slug="control",
            experiment_type="rollout",
            is_preview=False,
        )
    ]

    assert result == expected_result


@pytest.mark.asyncio
async def test_enrollment_metrics_recorded_with_compute_features_v1(
    client, mocker, recipes
):
    record_spy = mocker.spy(app.state.enrollment_ping, "record")
    context = json.dumps(
        {
            "app_id": "org.mozilla.test",
            "app_name": "test_app",
            "channel": "release",
        }
    )
    sdk = SDK(
        context=context,
        coenrolling_feature_ids=[],
        metrics_handler=CirrusMetricsHandler(app.state.enrollment_status_ping),
    )

    request_data = {
        "client_id": "test_client_id",
        "context": {"user_id": "test-client-id"},
    }

    app.state.remote_setting_live.update_recipes(recipes)
    sdk.set_experiments(json.dumps(recipes))

    mocker.patch.object(app.state, "sdk_live", sdk)

    response = client.post("/v1/features/", json=request_data)
    assert response.status_code == 200
    record_spy.assert_called_once()
    call = record_spy.mock_calls[0]
    assert call.kwargs.get("nimbus_nimbus_user_id") == "test_client_id"
    assert len(events := call.kwargs["events"]) == 2
    assert events[0]["extra"]["is_preview"] == "false"
    assert events[1]["extra"]["is_preview"] == "false"

    record_spy.reset_mock()
    app.state.remote_setting_preview.update_recipes(recipes)
    mocker.patch.object(app.state, "sdk_preview", sdk)

    response = client.post("/v1/features/?nimbus_preview=true", json=request_data)
    assert response.status_code == 200
    record_spy.assert_called_once()
    call = record_spy.mock_calls[0]
    assert call.kwargs.get("nimbus_nimbus_user_id") == "test_client_id"
    assert len(events := call.kwargs["events"]) == 2
    assert events[0]["extra"]["is_preview"] == "true"
    assert events[1]["extra"]["is_preview"] == "true"


@pytest.mark.asyncio
async def test_enrollment_metrics_recorded_with_compute_features_v2(
    client, mocker, recipes
):
    record_spy = mocker.spy(app.state.enrollment_ping, "record")
    context = json.dumps(
        {
            "app_id": "org.mozilla.test",
            "app_name": "test_app",
            "channel": "release",
        }
    )
    sdk = SDK(
        context=context,
        coenrolling_feature_ids=[],
        metrics_handler=CirrusMetricsHandler(app.state.enrollment_status_ping),
    )

    request_data = {
        "client_id": "test_client_id",
        "context": {"user_id": "test-client-id"},
    }

    app.state.remote_setting_live.update_recipes(recipes)
    sdk.set_experiments(json.dumps(recipes))

    mocker.patch.object(app.state, "sdk_live", sdk)

    response = client.post("/v2/features/", json=request_data)
    assert response.status_code == 200
    record_spy.assert_called_once()
    call = record_spy.mock_calls[0]
    assert call.kwargs.get("nimbus_nimbus_user_id") == "test_client_id"
    assert len(events := call.kwargs["events"]) == 2
    assert events[0]["extra"]["is_preview"] == "false"
    assert events[1]["extra"]["is_preview"] == "false"

    record_spy.reset_mock()
    app.state.remote_setting_preview.update_recipes(recipes)
    mocker.patch.object(app.state, "sdk_preview", sdk)

    response = client.post("/v2/features/?nimbus_preview=true", json=request_data)
    assert response.status_code == 200
    record_spy.assert_called_once()
    call = record_spy.mock_calls[0]
    assert call.kwargs.get("nimbus_nimbus_user_id") == "test_client_id"
    assert len(events := call.kwargs["events"]) == 2
    assert events[0]["extra"]["is_preview"] == "true"
    assert events[1]["extra"]["is_preview"] == "true"


@pytest.mark.asyncio
async def test_enrollment_status_metrics_recorded_with_metrics_handler_v1(
    client, mocker, recipes
):
    record_spy = mocker.spy(app.state.enrollment_status_ping, "record")
    context = json.dumps(
        {
            "app_id": "org.mozilla.test",
            "app_name": "test_app",
            "channel": "release",
        }
    )
    sdk = SDK(
        context=context,
        coenrolling_feature_ids=[],
        metrics_handler=CirrusMetricsHandler(app.state.enrollment_status_ping),
    )

    request_data = {
        "client_id": "test_client_id",
        "context": {"user_id": "test-client-id"},
    }

    app.state.remote_setting_live.update_recipes(recipes)
    sdk.set_experiments(json.dumps(recipes))

    mocker.patch.object(app.state, "sdk_live", sdk)

    response = client.post("/v1/features/", json=request_data)
    assert response.status_code == 200
    record_spy.assert_called_once()
    assert len(events := record_spy.mock_calls[0].kwargs["events"]) == 5
    assert events[0]["extra"]["status"] == "Enrolled"
    assert events[1]["extra"]["status"] == "Enrolled"
    assert events[2]["extra"]["status"] == "NotEnrolled"
    assert events[2]["extra"]["reason"] == "NotSelected"
    assert events[3]["extra"]["status"] == "NotEnrolled"
    assert events[3]["extra"]["reason"] == "NotTargeted"
    assert events[4]["extra"]["status"] == "Error"

    record_spy.reset_mock()
    app.state.remote_setting_preview.update_recipes(recipes)
    mocker.patch.object(app.state, "sdk_preview", sdk)

    response = client.post("/v1/features/?nimbus_preview=true", json=request_data)
    assert response.status_code == 200
    record_spy.assert_called_once()
    assert len(events := record_spy.mock_calls[0].kwargs["events"]) == 5
    assert events[0]["extra"]["status"] == "Enrolled"
    assert events[1]["extra"]["status"] == "Enrolled"
    assert events[2]["extra"]["status"] == "NotEnrolled"
    assert events[2]["extra"]["reason"] == "NotSelected"
    assert events[3]["extra"]["status"] == "NotEnrolled"
    assert events[3]["extra"]["reason"] == "NotTargeted"
    assert events[4]["extra"]["status"] == "Error"


@pytest.mark.asyncio
async def test_enrollment_status_metrics_recorded_with_metrics_handler_v2(
    client, mocker, recipes
):
    record_spy = mocker.spy(app.state.enrollment_status_ping, "record")
    context = json.dumps(
        {
            "app_id": "org.mozilla.test",
            "app_name": "test_app",
            "channel": "release",
        }
    )
    sdk = SDK(
        context=context,
        coenrolling_feature_ids=[],
        metrics_handler=CirrusMetricsHandler(app.state.enrollment_status_ping),
    )

    request_data = {
        "client_id": "test_client_id",
        "context": {"user_id": "test-client-id"},
    }

    app.state.remote_setting_live.update_recipes(recipes)
    sdk.set_experiments(json.dumps(recipes))

    mocker.patch.object(app.state, "sdk_live", sdk)

    response = client.post("/v2/features/", json=request_data)
    assert response.status_code == 200
    record_spy.assert_called_once()
    assert len(events := record_spy.mock_calls[0].kwargs["events"]) == 5
    assert events[0]["extra"]["status"] == "Enrolled"
    assert events[1]["extra"]["status"] == "Enrolled"
    assert events[2]["extra"]["status"] == "NotEnrolled"
    assert events[2]["extra"]["reason"] == "NotSelected"
    assert events[3]["extra"]["status"] == "NotEnrolled"
    assert events[3]["extra"]["reason"] == "NotTargeted"
    assert events[4]["extra"]["status"] == "Error"

    record_spy.reset_mock()
    app.state.remote_setting_preview.update_recipes(recipes)
    mocker.patch.object(app.state, "sdk_preview", sdk)

    response = client.post("/v2/features/?nimbus_preview=true", json=request_data)
    assert response.status_code == 200
    record_spy.assert_called_once()
    assert len(events := record_spy.mock_calls[0].kwargs["events"]) == 5
    assert events[0]["extra"]["status"] == "Enrolled"
    assert events[1]["extra"]["status"] == "Enrolled"
    assert events[2]["extra"]["status"] == "NotEnrolled"
    assert events[2]["extra"]["reason"] == "NotSelected"
    assert events[3]["extra"]["status"] == "NotEnrolled"
    assert events[3]["extra"]["reason"] == "NotTargeted"
    assert events[4]["extra"]["status"] == "Error"


def test_instance_name_metric(mocker):
    startup_ping = mocker.patch("cirrus.main.app.state.startup_ping")
    send_instance_name_metric()
    startup_ping.record.assert_called_once()
