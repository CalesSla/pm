import pytest
from fastapi.testclient import TestClient

from app.api.auth import sessions
from app.main import app


@pytest.fixture(autouse=True)
def clear_sessions():
    sessions.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_login_valid_credentials(client):
    resp = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "user"
    assert "session" in resp.cookies


def test_login_invalid_credentials(client):
    resp = client.post("/api/auth/login", json={"username": "user", "password": "wrong"})
    assert resp.status_code == 401


def test_me_authenticated(client):
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "user"


def test_me_unauthenticated(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout(client):
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    client.post("/api/auth/logout")
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
