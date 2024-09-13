from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthcheck():
    response = client.get("/healthcheck")
    response_obj = response.json()

    assert response.status_code == 200
    assert response_obj == {"message": "healthcheck successful"}
