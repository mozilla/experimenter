from cirrus.main import get_metrics_data, initialize_glean
from glean.testing import ErrorType


def test_record_metrics(remote_settings, recipes):
    remote_settings.update_recipes(recipes)
    _, metrics = initialize_glean()
    enrolled_partial_configuration = {
        "enrolledFeatureConfigMap": {
            "feature_name": {
                "branch": "treatment",
                "feature": {
                    "featureId": "feature_name",
                    "value": {"enabled": True},
                },
                "featureId": "feature_name",
                "slug": "experiment_slug",
            }
        },
        "enrollments": [
            {
                "slug": "experiment_slug",
                "status": {
                    "Enrolled": {
                        "branch": "treatment",
                        "enrollment_id": "enrollment_id",
                        "reason": "Qualified",
                    }
                },
            }
        ],
        "events": [
            {
                "branch_slug": "treatment",
                "change": "Enrollment",
                "enrollment_id": "enrollment_id",
                "experiment_slug": "experiment_slug",
                "reason": None,
            }
        ],
    }

    experiment_slug, branch_slug, enrollment_id, experiment_type = get_metrics_data(
        enrolled_partial_configuration,
    )

    metrics.cirrus_events.enrollment.record(
        metrics.cirrus_events.EnrollmentExtra(
            experiment_type=experiment_type,
            app_id="app_id",
            user_id="client_id",
            experiment=experiment_slug,
            branch=branch_slug,
            enrollment_id=enrollment_id,
        )
    )

    assert (
        metrics.cirrus_events.enrollment.test_get_num_recorded_errors(
            ErrorType.INVALID_OVERFLOW
        )
        == 0
    )
    snapshot = metrics.cirrus_events.enrollment.test_get_value()
    assert len(snapshot) == 1
    assert snapshot[0].name == "enrollment"
