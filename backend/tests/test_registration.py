def test_register_new_user(client):
    resp = client.post("/api/auth/register", json={
        "username": "newuser",
        "password": "secret",
        "display_name": "New User",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "newuser"
    assert data["display_name"] == "New User"
    assert "session" in resp.cookies


def test_register_creates_default_board(client):
    client.post("/api/auth/register", json={"username": "newuser", "password": "secret"})
    resp = client.get("/api/boards")
    assert resp.status_code == 200
    boards = resp.json()["boards"]
    assert len(boards) == 1
    assert boards[0]["title"] == "My Board"


def test_register_creates_board_with_columns(client):
    client.post("/api/auth/register", json={"username": "newuser", "password": "secret"})
    resp = client.get("/api/board")
    data = resp.json()
    assert len(data["columns"]) == 5
    assert data["columns"][0]["title"] == "Backlog"
    assert data["columns"][4]["title"] == "Done"


def test_register_default_display_name(client):
    resp = client.post("/api/auth/register", json={"username": "alice", "password": "secret"})
    assert resp.json()["display_name"] == "alice"


def test_register_duplicate_username(client):
    client.post("/api/auth/register", json={"username": "dup", "password": "secret"})
    resp = client.post("/api/auth/register", json={"username": "dup", "password": "other"})
    assert resp.status_code == 409


def test_register_short_username(client):
    resp = client.post("/api/auth/register", json={"username": "a", "password": "secret"})
    assert resp.status_code == 400


def test_register_short_password(client):
    resp = client.post("/api/auth/register", json={"username": "valid", "password": "ab"})
    assert resp.status_code == 400


def test_register_then_login(client):
    client.post("/api/auth/register", json={"username": "logintest", "password": "pass1234"})
    # Logout first
    client.post("/api/auth/logout")
    resp = client.post("/api/auth/login", json={"username": "logintest", "password": "pass1234"})
    assert resp.status_code == 200


def test_me_returns_display_name(authed_client):
    resp = authed_client.get("/api/auth/me")
    data = resp.json()
    assert "display_name" in data
    assert data["username"] == "user"
