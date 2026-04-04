import re


def db_id(prefixed: str) -> int:
    return int(re.sub(r"^(col-|card-)", "", prefixed))


def _setup(authed_client):
    """Set up: create second user, add as member, return (board_id, card_db_id, alice_id)."""
    from fastapi.testclient import TestClient
    from app.main import app

    # Use a separate client to register alice so we don't overwrite authed_client's session
    other = TestClient(app)
    other.post("/api/auth/register", json={"username": "alice", "password": "pass1234", "display_name": "Alice"})

    boards = authed_client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]
    member = authed_client.post(f"/api/boards/{board_id}/members", json={"username": "alice"}).json()
    alice_id = member["id"]

    board = authed_client.get(f"/api/boards/{board_id}").json()
    card_id = db_id(board["columns"][0]["cardIds"][0])
    return board_id, card_id, alice_id


def test_assign_card(authed_client):
    board_id, card_id, alice_id = _setup(authed_client)
    resp = authed_client.post(f"/api/cards/{card_id}/assign", json={"user_id": alice_id})
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_assignees_in_board_response(authed_client):
    board_id, card_id, alice_id = _setup(authed_client)
    authed_client.post(f"/api/cards/{card_id}/assign", json={"user_id": alice_id})

    board = authed_client.get(f"/api/boards/{board_id}").json()
    card_key = f"card-{card_id}"
    assert len(board["cards"][card_key]["assignees"]) == 1
    assert board["cards"][card_key]["assignees"][0]["username"] == "alice"


def test_unassign_card(authed_client):
    board_id, card_id, alice_id = _setup(authed_client)
    authed_client.post(f"/api/cards/{card_id}/assign", json={"user_id": alice_id})

    resp = authed_client.delete(f"/api/cards/{card_id}/assign/{alice_id}")
    assert resp.status_code == 200

    board = authed_client.get(f"/api/boards/{board_id}").json()
    card_key = f"card-{card_id}"
    assert len(board["cards"][card_key]["assignees"]) == 0


def test_assign_owner(authed_client):
    boards = authed_client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]
    board = authed_client.get(f"/api/boards/{board_id}").json()
    card_id = db_id(board["columns"][0]["cardIds"][0])
    owner_id = board["members"][0]["id"]

    resp = authed_client.post(f"/api/cards/{card_id}/assign", json={"user_id": owner_id})
    assert resp.status_code == 200


def test_cannot_assign_non_member(authed_client):
    boards = authed_client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]
    board = authed_client.get(f"/api/boards/{board_id}").json()
    card_id = db_id(board["columns"][0]["cardIds"][0])

    # Register a stranger via separate client
    from fastapi.testclient import TestClient
    from app.main import app
    other = TestClient(app)
    other.post("/api/auth/register", json={"username": "stranger", "password": "pass1234"})

    # user_id 999 doesn't exist, should fail
    resp = authed_client.post(f"/api/cards/{card_id}/assign", json={"user_id": 999})
    assert resp.status_code == 400


def test_duplicate_assignment_idempotent(authed_client):
    board_id, card_id, alice_id = _setup(authed_client)
    authed_client.post(f"/api/cards/{card_id}/assign", json={"user_id": alice_id})
    resp = authed_client.post(f"/api/cards/{card_id}/assign", json={"user_id": alice_id})
    assert resp.status_code == 200

    board = authed_client.get(f"/api/boards/{board_id}").json()
    card_key = f"card-{card_id}"
    assert len(board["cards"][card_key]["assignees"]) == 1


def test_assignments_unauthenticated(client):
    resp = client.post("/api/cards/1/assign", json={"user_id": 1})
    assert resp.status_code == 401

    resp = client.delete("/api/cards/1/assign/1")
    assert resp.status_code == 401
