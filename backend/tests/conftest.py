import pytest
from fastapi.testclient import TestClient

import app.db as db
from app.api.auth import sessions
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Use a fresh temporary database for every test."""
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", test_db)
    sessions.clear()
    db.init_db()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def authed_client(client):
    """Client that is already logged in as 'user'."""
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    return client
