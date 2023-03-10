from pytest import fixture
from fastapi.testclient import TestClient
from cirrus.main import app


@fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
