import logging
import os

from fastapi.testclient import TestClient

from app.constants import NON_CONSENTED_USER_ID, QDRANT_ANONYMOUS_ID_KEY
from app.main import app

logging.basicConfig(level=logging.DEBUG)

client = TestClient(app)

headers = {"x-api-key": os.getenv("API_AUTHENTICATION_KEY")}
json_body_template = {
    "anonymousId": "test_anonymous_id",
    "properties": {},
    "context": {},
    "integrations": {},
    "originalTimestamp": "",
}


# Happy Paths
def test_anonymous_id():
    response = client.get("/anonymous_id", headers=headers)
    response_obj = response.json()

    assert response.status_code == 200
    assert len(response_obj[QDRANT_ANONYMOUS_ID_KEY]) == 36


def test_identify():
    json_body_template["userId"] = "test_user_id"
    response = client.post("/identify", headers=headers, json=json_body_template)
    response_obj = response.json()

    assert response.status_code == 200
    assert "User identified successfully" == response_obj["message"]


def test_page():
    json_body_template["category"] = "test category"
    json_body_template["name"] = "test name"
    json_body_template["properties"]["title"] = "test title"
    json_body_template["properties"]["url"] = "https://testurl.com"

    response = client.post("/page", headers=headers, json=json_body_template)
    response_obj = response.json()

    assert response.status_code == 200
    assert "Page view tracked successfully" == response_obj["message"]


def test_track():
    json_body_template["event"] = "interaction"
    response = client.post("/track", headers=headers, json=json_body_template)
    response_obj = response.json()

    assert response.status_code == 200
    assert "Event tracked successfully" == response_obj["message"]


# Sad Paths
def test_anonymous_id_no_auth():
    response = client.get("/anonymous_id", headers={})
    response_obj = response.json()

    assert response.status_code == 401
    assert response_obj["detail"] == "Unauthorized"


def test_identify_empty_body():
    response = client.post("/identify", headers=headers, json={})
    response_obj = response.json()

    assert response.status_code == 200
    assert (
        f"User ({NON_CONSENTED_USER_ID}) was not identified" == response_obj["message"]
    )
