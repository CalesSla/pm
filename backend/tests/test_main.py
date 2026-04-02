import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def static_dir(tmp_path):
    index = tmp_path / "index.html"
    index.write_text("<html><body>Kanban</body></html>")
    css_dir = tmp_path / "_next" / "static"
    css_dir.mkdir(parents=True)
    (css_dir / "test.css").write_text("body{}")
    return tmp_path


@pytest.fixture
def client(static_dir, monkeypatch):
    monkeypatch.setenv("STATIC_DIR", str(static_dir))
    # Re-import to pick up new STATIC_DIR
    import importlib
    import app.main
    importlib.reload(app.main)
    return TestClient(app.main.app)


@pytest.fixture
def client_no_static(tmp_path, monkeypatch):
    empty = tmp_path / "nonexistent"
    monkeypatch.setenv("STATIC_DIR", str(empty))
    import importlib
    import app.main
    importlib.reload(app.main)
    return TestClient(app.main.app)


def test_index_serves_static_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Kanban" in resp.text


def test_index_fallback_when_no_static(client_no_static):
    resp = client_no_static.get("/")
    assert resp.status_code == 200
    assert "not built yet" in resp.text


def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_takes_precedence_over_static(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_static_assets_served(client):
    resp = client.get("/_next/static/test.css")
    assert resp.status_code == 200
    assert "body{}" in resp.text
