import re


def db_id(prefixed: str) -> int:
    return int(re.sub(r"^(col-|card-)", "", prefixed))


def test_create_column(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    resp = authed_client.post("/api/columns", json={"board_id": board_id, "title": "Blocked"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Blocked"
    assert data["position"] == 5  # After the 5 default columns (0-4)

    board = authed_client.get(f"/api/boards/{board_id}").json()
    assert len(board["columns"]) == 6
    assert board["columns"][-1]["title"] == "Blocked"


def test_create_column_unauthenticated(client):
    resp = client.post("/api/columns", json={"board_id": 1, "title": "Nope"})
    assert resp.status_code == 401


def test_create_column_wrong_board(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "pass1"})
    boards = client.get("/api/boards").json()["boards"]
    alice_board_id = boards[0]["id"]
    client.post("/api/auth/logout")

    client.post("/api/auth/register", json={"username": "bob", "password": "pass2"})
    resp = client.post("/api/columns", json={"board_id": alice_board_id, "title": "Nope"})
    assert resp.status_code == 404


def test_delete_column(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    board = authed_client.get(f"/api/boards/{board_id}").json()
    last_col_id = db_id(board["columns"][-1]["id"])

    resp = authed_client.delete(f"/api/columns/{last_col_id}")
    assert resp.status_code == 200

    board = authed_client.get(f"/api/boards/{board_id}").json()
    assert len(board["columns"]) == 4


def test_delete_column_cascades_cards(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    board = authed_client.get(f"/api/boards/{board_id}").json()
    # Backlog has 2 cards
    col = board["columns"][0]
    assert len(col["cardIds"]) == 2
    total_cards = len(board["cards"])

    col_id = db_id(col["id"])
    authed_client.delete(f"/api/columns/{col_id}")

    board = authed_client.get(f"/api/boards/{board_id}").json()
    assert len(board["cards"]) == total_cards - 2


def test_delete_column_adjusts_positions(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    board = authed_client.get(f"/api/boards/{board_id}").json()

    # Delete the second column (Discovery, position 1)
    second_col_id = db_id(board["columns"][1]["id"])
    authed_client.delete(f"/api/columns/{second_col_id}")

    board = authed_client.get(f"/api/boards/{board_id}").json()
    assert len(board["columns"]) == 4
    # The third column should now be at position 1 in the list
    assert board["columns"][1]["title"] == "In Progress"


def test_delete_column_unauthenticated(client):
    resp = client.delete("/api/columns/1")
    assert resp.status_code == 401
