def test_update_display_name(authed_client):
    res = authed_client.put("/api/auth/profile", json={"display_name": "New Name"})
    assert res.status_code == 200
    assert res.json()["display_name"] == "New Name"

    # Verify persisted
    me = authed_client.get("/api/auth/me")
    assert me.json()["display_name"] == "New Name"


def test_update_display_name_empty_rejected(authed_client):
    res = authed_client.put("/api/auth/profile", json={"display_name": "  "})
    assert res.status_code == 400


def test_update_display_name_unauthenticated(client):
    res = client.put("/api/auth/profile", json={"display_name": "Name"})
    assert res.status_code == 401


def test_change_password(authed_client):
    res = authed_client.put(
        "/api/auth/password",
        json={"current_password": "password", "new_password": "newpass123"},
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True

    # Login with new password
    authed_client.post("/api/auth/logout")
    login = authed_client.post("/api/auth/login", json={"username": "user", "password": "newpass123"})
    assert login.status_code == 200


def test_change_password_wrong_current(authed_client):
    res = authed_client.put(
        "/api/auth/password",
        json={"current_password": "wrong", "new_password": "newpass123"},
    )
    assert res.status_code == 403


def test_change_password_too_short(authed_client):
    res = authed_client.put(
        "/api/auth/password",
        json={"current_password": "password", "new_password": "ab"},
    )
    assert res.status_code == 400


def test_change_password_unauthenticated(client):
    res = client.put(
        "/api/auth/password",
        json={"current_password": "password", "new_password": "newpass123"},
    )
    assert res.status_code == 401
