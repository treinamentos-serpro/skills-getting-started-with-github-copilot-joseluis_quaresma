import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "activities",
        {
            "Chess Club": {
                "description": "Learn chess",
                "schedule": "Fridays",
                "max_participants": 12,
                "participants": ["existing@example.com"],
            }
        },
    )
    return TestClient(app_module.app)


def test_root_redirects_to_static_homepage(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == ["existing@example.com"]


def test_signup_adds_student_to_activity(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Signed up new@example.com for Chess Club"}
    assert "new@example.com" in app_module.activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_student(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_student_from_activity(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered existing@example.com from Chess Club"
    }
    assert app_module.activities["Chess Club"]["participants"] == []


def test_unregister_rejects_student_not_signed_up(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "absent@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}