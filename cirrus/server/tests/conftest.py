from fastapi.testclient import TestClient
from pytest import fixture

from cirrus.main import app


@fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
