from unittest import mock

from fastapi.testclient import TestClient
from glean import testing
from mozilla_nimbus_shared import check_schema
from pytest import fixture

from cirrus.experiment_recipes import RemoteSettings
from cirrus.feature_manifest import FeatureManifestLanguage
from cirrus.main import app, initialize_glean
from cirrus.sdk import SDK
from cirrus.settings import channel, context, fml_path


@fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@fixture
def scheduler_mock():
    with mock.patch("cirrus.main.app.state.scheduler") as scheduler_mock:
        yield scheduler_mock


@fixture
def remote_setting_mock():
    with mock.patch("cirrus.main.app.state.remote_setting") as remote_setting_mock:
        yield remote_setting_mock


@fixture
def remote_settings(sdk):
    return RemoteSettings(sdk)


@fixture
def sdk():
    return SDK(context=context)


@fixture
def fml_setup(fml, sdk):
    yield fml, sdk


@fixture
def fml():
    return FeatureManifestLanguage(fml_path, channel)


@fixture
def exception():
    return Exception("some error")


@fixture(name="reset_glean", scope="function", autouse=True)
def fixture_reset_glean():
    testing.reset_glean(application_id="cirrus-test", application_version="0.1.0")


@fixture
def get_telemetry():
    return initialize_glean()


@fixture
def create_recipe():
    def _create(
        slug="test",
        app_id="org.mozilla.test",
        app_name="test_app",
        channel="release",
        feature="test-feature",
        is_rollout=False,
        targeting="true",
        bucket_count=10000,
        bucket_start=0,
        bucket_total=10000,
        bucket_randomization_unit="user_id",
        is_enrollment_paused=False,
    ):
        recipe = {
            "slug": slug,
            "appId": app_id,
            "appName": app_name,
            "channel": channel,
            "endDate": None,
            "locales": None,
            "branches": [
                {
                    "slug": "control",
                    "ratio": 1,
                    "features": [
                        {
                            "value": {"enabled": True},
                            "featureId": feature,
                        }
                    ],
                }
            ],
            "outcomes": [],
            "arguments": {},
            "isRollout": is_rollout,
            "probeSets": [],
            "startDate": "2023-07-05",
            "targeting": targeting,
            "featureIds": [feature],
            "application": app_id,
            "bucketConfig": {
                "count": bucket_count,
                "start": bucket_start,
                "total": bucket_total,
                "namespace": feature + "-" + slug,
                "randomizationUnit": bucket_randomization_unit,
            },
            "localizations": None,
            "schemaVersion": "1.12.0",
            "userFacingName": "",
            "referenceBranch": "control",
            "proposedDuration": 28,
            "enrollmentEndDate": "2023-07-12",
            "isEnrollmentPaused": is_enrollment_paused,
            "proposedEnrollment": 7,
            "userFacingDescription": "",
            "featureValidationOptOut": False,
            "id": slug,
            "last_modified": 1689000336881,
        }
        check_schema("experiments/NimbusExperiment", recipe)
        return recipe

    return _create


@fixture
def recipes(create_recipe):
    return {
        "data": [
            create_recipe(slug="cirrus-test-1", feature="feature-1", is_rollout=True),
            create_recipe(slug="cirrus-test-2", feature="feature-2"),
            create_recipe(slug="cirrus-test-3", feature="feature-3", bucket_count=1),
            create_recipe(slug="cirrus-test-4", feature="feature-4", targeting="false"),
            create_recipe(
                slug="cirrus-test-5", feature="feature-5", targeting="random_value"
            ),
        ]
    }
