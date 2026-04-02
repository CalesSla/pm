def test_login_valid_credentials(client):
    resp = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "user"
    assert "session" in resp.cookies


def test_login_invalid_credentials(client):
    resp = client.post("/api/auth/login", json={"username": "user", "password": "wrong"})
    assert resp.status_code == 401


def test_me_authenticated(authed_client):
    resp = authed_client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "user"


def test_me_unauthenticated(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout(authed_client):
    authed_client.post("/api/auth/logout")
    resp = authed_client.get("/api/auth/me")
    assert resp.status_code == 401
