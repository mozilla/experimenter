from unittest import mock

from fastapi.testclient import TestClient
from pytest import fixture

from cirrus.experiment_recipes import RemoteSettings
from cirrus.feature_manifest import FeatureManifestLanguage
from cirrus.main import app, initialize_glean
from cirrus.sdk import SDK
from cirrus.settings import channel, context, fml_path
from glean import testing


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
def recipes():
    return {
        "data": [
            {
                "slug": "cirrus-test-1",
                "appId": "org.mozilla.test",
                "appName": "test_app",
                "channel": "release",
                "endDate": None,
                "locales": None,
                "branches": [
                    {
                        "slug": "control",
                        "ratio": 1,
                        "feature": {
                            "value": [{"enabled": True}, {"enabled": True}],
                            "featureId": "coordinators-refactor-feature",
                        },
                    }
                ],
                "outcomes": [],
                "arguments": {},
                "isRollout": True,
                "probeSets": [],
                "startDate": "2023-07-05",
                "targeting": "(app_version|versionCompare('115.!') >= 0)",
                "featureIds": ["coordinators-refactor-feature"],
                "application": "org.mozilla.test",
                "bucketConfig": {"count": 2000, "start": 1500, "total": 10000},
                "namespace": "cirrus-test-1-feature-release-no_targeting-rollout-1",
                "randomizationUnit": "nimbus_id",
                "localizations": None,
                "schemaVersion": "1.12.0",
                "userFacingName": "Rollout 2",
                "referenceBranch": "control",
                "proposedDuration": 28,
                "enrollmentEndDate": "2023-07-12",
                "isEnrollmentPaused": False,
                "proposedEnrollment": 7,
                "userFacingDescription": "Rollout of coordinators refactor.",
                "featureValidationOptOut": False,
                "id": "cirrus-test-1",
                "last_modified": 1689000336881,
            },
            {
                "slug": "cirrus-test-2",
                "appId": "org.mozilla.test",
                "appName": "test_app",
                "channel": "release",
                "endDate": None,
                "locales": None,
                "branches": [
                    {
                        "slug": "control-off-branch",
                        "ratio": 1,
                        "feature": {
                            "value": [{"enabled": False}, {"enabled": True}],
                            "featureId": "re-engagement-notification",
                        },
                    },
                    {
                        "slug": "treatment-privacy-notification",
                        "ratio": 1,
                        "feature": {
                            "value": [
                                {"type": 0},
                                {"enabled": True},
                                {"enabled": True},
                            ],
                            "featureId": "re-engagement-notification",
                        },
                    },
                ],
                "outcomes": [],
                "arguments": {},
                "isRollout": False,
                "probeSets": [],
                "targeting": "((is_already_enrolled) || ((isFirstRun == 'true') && (app_version|versionCompare('115.!') >= 0)))",
                "featureIds": ["re-engagement-notification"],
                "application": "org.mozilla.test",
                "bucketConfig": {"count": 5000, "start": 5000, "total": 10000},
                "namespace": "cirrus-test-2-release-3",
                "randomizationUnit": "nimbus_id",
                "localizations": None,
                "schemaVersion": "1.12.0",
                "userFacingName": "timing v2",
                "referenceBranch": "control-off-branch",
                "proposedDuration": 30,
                "enrollmentEndDate": "2023-07-18",
                "isEnrollmentPaused": False,
                "proposedEnrollment": 14,
                "userFacingDescription": "Testing timing of how we enable re-engagement notifications.",
                "featureValidationOptOut": False,
                "id": "test-cirrus-2",
                "last_modified": 1687965974945,
            },
        ]
    }
