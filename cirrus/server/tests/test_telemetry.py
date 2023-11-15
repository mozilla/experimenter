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
)
from cirrus.sdk import SDK


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
    _, metrics = initialize_glean()
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
    context = json.dumps(
        {
            "app_id": "org.mozilla.test",
            "app_name": "test_app",
            "channel": "release",
        }
    )
    sdk = SDK(context=context, coenrolling_feature_ids=[])

    request = FeatureRequest(
        client_id="test_client_id", context={"user_id": "test-client-id"}
    )

    app.state.remote_setting.update_recipes(recipes)
    sdk.set_experiments(json.dumps(recipes))
    _, metrics = initialize_glean()

    app.state.pings.enrollment.test_before_next_submit(before_enrollment_ping)

    mocker.patch.object(app.state, "sdk", sdk)
    ping_spy = mocker.spy(app.state.pings.enrollment, "submit")

    await compute_features(request)

    assert ping_spy.call_count == 1
    assert app.state.metrics.cirrus_events.enrollment.test_get_value() is None
