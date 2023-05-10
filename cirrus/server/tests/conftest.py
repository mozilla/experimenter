from unittest import mock

from fastapi.testclient import TestClient
from pytest import fixture

from ..cirrus.main import app


@fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@fixture
def scheduler_mock():
    with mock.patch("cirrus.server.cirrus.main.scheduler") as scheduler_mock:
        yield scheduler_mock


@fixture
def remote_setting_mock():
    with mock.patch("cirrus.server.cirrus.main.remote_setting") as remote_setting_mock:
        yield remote_setting_mock


@fixture
def exception():
    return Exception("some error")
