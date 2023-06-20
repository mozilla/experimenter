from unittest import mock

from fastapi.testclient import TestClient
from pytest import fixture

from cirrus.experiment_recipes import RemoteSettings
from cirrus.feature_manifest import FeatureManifestLanguage
from cirrus.main import app
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
def remote_setting(sdk):
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
