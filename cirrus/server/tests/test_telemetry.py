import json

import pytest
from glean.testing import ErrorType

from cirrus.experiment_recipes import RecipeType
from cirrus.main import (
    app,
    initialize_glean,
    record_metrics,
    send_instance_name_metric,
)
from cirrus.sdk import SDK, CirrusMetricsHandler


def before_enrollment_ping(data):
    assert (
        app.state.metrics.cirrus_events.enrollment.test_get_num_recorded_errors(
            ErrorType.INVALID_OVERFLOW
        )
        == 0
    )
    snapshot = app.state.metrics.cirrus_events.enrollment.test_get_value()
    assert len(snapshot) == 2

    extra_1 = snapshot[0].extra
    assert extra_1["app_id"] == "test_app_id"
    assert extra_1["user_id"] == "test_client_id"
    assert extra_1["experiment"] == "cirrus-test-1"
    assert extra_1["branch"] == "control"
    assert extra_1["experiment_type"] == RecipeType.ROLLOUT.value
    assert extra_1["is_preview"] == "false"

    extra_2 = snapshot[1].extra
    assert extra_2["app_id"] == "test_app_id"
    assert extra_2["user_id"] == "test_client_id"
    assert extra_2["experiment"] == "cirrus-test-2"
    assert extra_2["branch"] == "control"
    assert extra_2["experiment_type"] == RecipeType.EXPERIMENT.value
    assert extra_2["is_preview"] == "false"


@pytest.mark.asyncio
async def test_enrollment_metrics_recorded_with_record_metrics(mocker, recipes):
    app.state.remote_setting_live.update_recipes(recipes)
    ping_spy = mocker.spy(app.state.pings.enrollment, "submit")
    enrolled_partial_configuration = {
        "events": [
            {
                "branch_slug": "control",
                "change": "Enrollment",
                "enrollment_id": "enrollment_id",
                "experiment_slug": "cirrus-test-1",
                "reason": None,
            },
            {
                "branch_slug": "control",
                "change": "Enrollment",
                "enrollment_id": "enrollment_id",
                "experiment_slug": "cirrus-test-2",
                "reason": None,
            },
            {
                "branch_slug": "",
                "change": "EnrollFailed",
                "enrollment_id": "blah",
                "experiment_slug": "fake-experiment",
                "reason": "not_selected",
            },
        ],
    }

    app.state.pings.enrollment.test_before_next_submit(before_enrollment_ping)

    await record_metrics(
        enrolled_partial_configuration, "test_client_id", nimbus_preview_flag=False
    )

    assert ping_spy.call_count == 1
    assert app.state.metrics.cirrus_events.enrollment.test_get_value() is None


@pytest.mark.asyncio
async def test_enrollment_metrics_recorded_with_compute_features(client, mocker, recipes):
    _, app.state.metrics = initialize_glean()
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
        metrics_handler=CirrusMetricsHandler(app.state.metrics, app.state.pings),
    )

    request_data = {
        "client_id": "test_client_id",
        "context": {"user_id": "test-client-id"},
    }

    app.state.remote_setting_live.update_recipes(recipes)
    sdk.set_experiments(json.dumps(recipes))

    def validate_before_submit(data):
        snapshot = app.state.metrics.cirrus_events.enrollment.test_get_value()
        assert snapshot is not None
        assert len(snapshot) == 2
        assert snapshot[0].extra["is_preview"] == "false"
        assert snapshot[1].extra["is_preview"] == "false"

    app.state.pings.enrollment.test_before_next_submit(validate_before_submit)

    mocker.patch.object(app.state, "sdk_live", sdk)
    ping_spy = mocker.spy(app.state.pings.enrollment, "submit")

    response = client.post("/v1/features/", json=request_data)
    assert response.status_code == 200
    assert ping_spy.call_count == 1
    assert app.state.metrics.cirrus_events.enrollment.test_get_value() is None

    ping_spy.reset_mock()

    app.state.remote_setting_preview.update_recipes(recipes)
    mocker.patch.object(app.state, "sdk_preview", sdk)

    def validate_before_submit_preview(data):
        snapshot = app.state.metrics.cirrus_events.enrollment.test_get_value()
        assert snapshot is not None
        assert len(snapshot) == 2
        assert snapshot[0].extra["is_preview"] == "true"
        assert snapshot[1].extra["is_preview"] == "true"

    app.state.pings.enrollment.test_before_next_submit(validate_before_submit_preview)

    response = client.post("/v1/features/?nimbus_preview=true", json=request_data)
    assert response.status_code == 200
    assert ping_spy.call_count == 1
    assert app.state.metrics.cirrus_events.enrollment.test_get_value() is None


@pytest.mark.asyncio
async def test_enrollment_status_metrics_recorded_with_metrics_handler(
    client, mocker, recipes
):
    _, app.state.metrics = initialize_glean()
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
        metrics_handler=CirrusMetricsHandler(app.state.metrics, app.state.pings),
    )

    request_data = {
        "client_id": "test_client_id",
        "context": {"user_id": "test-client-id"},
    }

    app.state.remote_setting_live.update_recipes(recipes)
    sdk.set_experiments(json.dumps(recipes))

    def test_ping(data):
        assert (
            app.state.metrics.cirrus_events.enrollment_status.test_get_num_recorded_errors(
                ErrorType.INVALID_OVERFLOW
            )
            == 0
        )
        snapshot = app.state.metrics.cirrus_events.enrollment_status.test_get_value()
        assert len(snapshot) == 5
        assert snapshot[0].extra["status"] == "Enrolled"
        assert snapshot[1].extra["status"] == "Enrolled"
        assert snapshot[2].extra["status"] == "NotEnrolled"
        assert snapshot[2].extra["reason"] == "NotSelected"
        assert snapshot[3].extra["status"] == "NotEnrolled"
        assert snapshot[3].extra["reason"] == "NotTargeted"
        assert snapshot[4].extra["status"] == "Error"

    app.state.pings.enrollment_status.test_before_next_submit(test_ping)

    mocker.patch.object(app.state, "sdk_live", sdk)
    ping_spy = mocker.spy(app.state.pings.enrollment_status, "submit")

    response = client.post("/v1/features/", json=request_data)
    assert response.status_code == 200
    assert ping_spy.call_count == 1
    assert app.state.metrics.cirrus_events.enrollment_status.test_get_value() is None

    ping_spy.reset_mock()
    app.state.remote_setting_preview.update_recipes(recipes)
    mocker.patch.object(app.state, "sdk_preview", sdk)

    response = client.post("/v1/features/?nimbus_preview=true", json=request_data)
    assert response.status_code == 200
    assert ping_spy.call_count == 1
    assert app.state.metrics.cirrus_events.enrollment_status.test_get_value() is None


def test_instance_name_metric(mocker):
    app.state.pings, _ = initialize_glean()
    ping_spy = mocker.spy(app.state.pings.startup, "submit")
    send_instance_name_metric()
    assert ping_spy.call_count == 1
