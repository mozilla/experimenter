def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


def test_get_enrollment_status(client):
    response = client.get("/enrollment_status")
    assert response.status_code == 200
    assert response.json() == {"feature": "test"}
