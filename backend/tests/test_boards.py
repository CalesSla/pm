import re


def db_id(prefixed: str) -> int:
    return int(re.sub(r"^(col-|card-)", "", prefixed))


def test_list_boards(authed_client):
    resp = authed_client.get("/api/boards")
    assert resp.status_code == 200
    boards = resp.json()["boards"]
    assert len(boards) == 1
    assert boards[0]["title"] == "My Board"


def test_list_boards_unauthenticated(client):
    resp = client.get("/api/boards")
    assert resp.status_code == 401


def test_create_board(authed_client):
    resp = authed_client.post("/api/boards", json={"title": "Sprint 2"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Sprint 2"
    assert "id" in data

    boards = authed_client.get("/api/boards").json()["boards"]
    assert len(boards) == 2


def test_create_board_has_default_columns(authed_client):
    resp = authed_client.post("/api/boards", json={"title": "New Board"})
    board_id = resp.json()["id"]

    board = authed_client.get(f"/api/boards/{board_id}").json()
    assert len(board["columns"]) == 5
    assert board["columns"][0]["title"] == "Backlog"


def test_rename_board(authed_client):
    boards = authed_client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]
    resp = authed_client.put(f"/api/boards/{board_id}", json={"title": "Renamed"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Renamed"

    boards = authed_client.get("/api/boards").json()["boards"]
    assert boards[0]["title"] == "Renamed"


def test_delete_board(authed_client):
    # Create a second board then delete it
    resp = authed_client.post("/api/boards", json={"title": "Temp"})
    board_id = resp.json()["id"]

    resp = authed_client.delete(f"/api/boards/{board_id}")
    assert resp.status_code == 200

    boards = authed_client.get("/api/boards").json()["boards"]
    assert all(b["id"] != board_id for b in boards)


def test_delete_board_cascades_columns_and_cards(authed_client):
    resp = authed_client.post("/api/boards", json={"title": "Cascade Test"})
    board_id = resp.json()["id"]

    # Get a column from the new board and add a card
    board = authed_client.get(f"/api/boards/{board_id}").json()
    col_id = db_id(board["columns"][0]["id"])
    authed_client.post("/api/cards", json={"column_id": col_id, "title": "Will be deleted"})

    # Delete the board
    authed_client.delete(f"/api/boards/{board_id}")

    # The board should be gone
    resp = authed_client.get(f"/api/boards/{board_id}")
    assert resp.status_code == 404


def test_get_board_by_id(authed_client):
    boards = authed_client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]
    resp = authed_client.get(f"/api/boards/{board_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["columns"]) == 5
    assert len(data["cards"]) == 8


def test_get_board_not_owned(client):
    # Register two users
    client.post("/api/auth/register", json={"username": "alice", "password": "pass1"})
    boards = client.get("/api/boards").json()["boards"]
    alice_board_id = boards[0]["id"]
    client.post("/api/auth/logout")

    client.post("/api/auth/register", json={"username": "bob", "password": "pass2"})
    resp = client.get(f"/api/boards/{alice_board_id}")
    assert resp.status_code == 404


def test_board_isolation_between_users(client):
    """Cards on one user's board should not appear for another user."""
    client.post("/api/auth/register", json={"username": "user1", "password": "pass1"})
    board1 = client.get("/api/board").json()
    assert len(board1["cards"]) == 0  # New user, no seed cards
    client.post("/api/auth/logout")

    client.post("/api/auth/register", json={"username": "user2", "password": "pass2"})
    board2 = client.get("/api/board").json()
    assert len(board2["cards"]) == 0
