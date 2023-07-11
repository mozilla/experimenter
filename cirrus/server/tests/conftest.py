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
