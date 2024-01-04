import json

import pytest
from glean.testing import ErrorType

from cirrus.experiment_recipes import RecipeType
from cirrus.main import (
    FeatureRequest,
    app,
    compute_features,
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

    extra_2 = snapshot[1].extra
    assert extra_2["app_id"] == "test_app_id"
    assert extra_2["user_id"] == "test_client_id"
    assert extra_2["experiment"] == "cirrus-test-2"
    assert extra_2["branch"] == "control"
    assert extra_2["experiment_type"] == RecipeType.EXPERIMENT.value


@pytest.mark.asyncio
async def test_enrollment_metrics_recorded_with_record_metrics(mocker, recipes):
    app.state.remote_setting.update_recipes(recipes)
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

    await record_metrics(enrolled_partial_configuration, "test_client_id")

    assert ping_spy.call_count == 1
    assert app.state.metrics.cirrus_events.enrollment.test_get_value() is None


@pytest.mark.asyncio
async def test_enrollment_metrics_recorded_with_compute_features(mocker, recipes):
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

    request = FeatureRequest(
        client_id="test_client_id", context={"user_id": "test-client-id"}
    )

    app.state.remote_setting.update_recipes(recipes)
    sdk.set_experiments(json.dumps(recipes))

    app.state.pings.enrollment.test_before_next_submit(before_enrollment_ping)

    mocker.patch.object(app.state, "sdk", sdk)
    ping_spy = mocker.spy(app.state.pings.enrollment, "submit")

    await compute_features(request)

    assert ping_spy.call_count == 1
    assert app.state.metrics.cirrus_events.enrollment.test_get_value() is None


@pytest.mark.asyncio
async def test_enrollment_status_metrics_recorded_with_metrics_handler(mocker, recipes):
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

    request = FeatureRequest(
        client_id="test_client_id", context={"user_id": "test-client-id"}
    )

    app.state.remote_setting.update_recipes(recipes)
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

    mocker.patch.object(app.state, "sdk", sdk)
    ping_spy = mocker.spy(app.state.pings.enrollment_status, "submit")

    await compute_features(request)

    assert ping_spy.call_count == 1
    assert app.state.metrics.cirrus_events.enrollment_status.test_get_value() is None


def test_instance_name_metric(mocker):
    app.state.pings, _ = initialize_glean()
    ping_spy = mocker.spy(app.state.pings.startup, "submit")
    send_instance_name_metric()
    assert ping_spy.call_count == 1
