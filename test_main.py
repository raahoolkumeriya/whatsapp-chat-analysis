from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_home():
    response = client.get(
        "/", headers={"content-type": "text/html; charset=utf-8"})
    assert response.status_code == 200
    assert b"html" in response.content
    assert response.status_code == 200


def test_heartbeat():
    response = client.get("/heartbeat",
                          headers={"content-type": "text/html; charset=utf-8"})
    assert response.status_code == 200
    assert b"About" in response.content
