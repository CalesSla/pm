from fastapi.testclient import TestClient
from app.main import app


def _register_alice():
    """Register alice using a separate client so we don't clobber any sessions."""
    c = TestClient(app)
    c.post("/api/auth/register", json={"username": "alice", "password": "pass1234", "display_name": "Alice"})


def _alice_client() -> TestClient:
    """Return a client logged in as alice."""
    c = TestClient(app)
    c.post("/api/auth/login", json={"username": "alice", "password": "pass1234"})
    return c


def _setup(authed_client) -> int:
    _register_alice()
    boards = authed_client.get("/api/boards").json()["boards"]
    return boards[0]["id"]


def test_add_board_member(authed_client):
    board_id = _setup(authed_client)
    resp = authed_client.post(f"/api/boards/{board_id}/members", json={"username": "alice"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"
    assert resp.json()["role"] == "member"


def test_list_board_members(authed_client):
    board_id = _setup(authed_client)
    authed_client.post(f"/api/boards/{board_id}/members", json={"username": "alice"})

    resp = authed_client.get(f"/api/boards/{board_id}/members")
    assert resp.status_code == 200
    members = resp.json()["members"]
    assert len(members) == 2
    roles = {m["role"] for m in members}
    assert "owner" in roles
    assert "member" in roles


def test_remove_board_member(authed_client):
    board_id = _setup(authed_client)
    member = authed_client.post(f"/api/boards/{board_id}/members", json={"username": "alice"}).json()

    resp = authed_client.delete(f"/api/boards/{board_id}/members/{member['id']}")
    assert resp.status_code == 200

    members = authed_client.get(f"/api/boards/{board_id}/members").json()["members"]
    assert len(members) == 1


def test_members_in_board_response(authed_client):
    board_id = _setup(authed_client)
    authed_client.post(f"/api/boards/{board_id}/members", json={"username": "alice"})

    board = authed_client.get(f"/api/boards/{board_id}").json()
    assert "members" in board
    assert len(board["members"]) == 2


def test_shared_board_appears_in_member_list(authed_client):
    board_id = _setup(authed_client)
    authed_client.post(f"/api/boards/{board_id}/members", json={"username": "alice"})

    alice = _alice_client()
    boards = alice.get("/api/boards").json()["boards"]
    board_ids = [b["id"] for b in boards]
    assert board_id in board_ids


def test_member_can_view_shared_board(authed_client):
    board_id = _setup(authed_client)
    authed_client.post(f"/api/boards/{board_id}/members", json={"username": "alice"})

    alice = _alice_client()
    resp = alice.get(f"/api/boards/{board_id}")
    assert resp.status_code == 200
    assert "columns" in resp.json()


def test_non_member_cannot_view_board(authed_client):
    boards = authed_client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    bob = TestClient(app)
    bob.post("/api/auth/register", json={"username": "bob", "password": "pass1234"})
    resp = bob.get(f"/api/boards/{board_id}")
    assert resp.status_code == 404


def test_cannot_add_self_as_member(authed_client):
    boards = authed_client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]
    resp = authed_client.post(f"/api/boards/{board_id}/members", json={"username": "user"})
    assert resp.status_code == 400


def test_cannot_add_nonexistent_user(authed_client):
    boards = authed_client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]
    resp = authed_client.post(f"/api/boards/{board_id}/members", json={"username": "ghost"})
    assert resp.status_code == 404


def test_duplicate_member_rejected(authed_client):
    board_id = _setup(authed_client)
    authed_client.post(f"/api/boards/{board_id}/members", json={"username": "alice"})
    resp = authed_client.post(f"/api/boards/{board_id}/members", json={"username": "alice"})
    assert resp.status_code == 409


def test_only_owner_can_add_members(authed_client):
    board_id = _setup(authed_client)
    authed_client.post(f"/api/boards/{board_id}/members", json={"username": "alice"})

    # Register charlie
    charlie_c = TestClient(app)
    charlie_c.post("/api/auth/register", json={"username": "charlie", "password": "pass1234"})

    # Alice (member, not owner) should not be able to add members
    alice = _alice_client()
    resp = alice.post(f"/api/boards/{board_id}/members", json={"username": "charlie"})
    assert resp.status_code == 403


def test_members_unauthenticated(client):
    resp = client.get("/api/boards/1/members")
    assert resp.status_code == 401

    resp = client.post("/api/boards/1/members", json={"username": "test"})
    assert resp.status_code == 401
