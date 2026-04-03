import re


def db_id(prefixed: str) -> int:
    return int(re.sub(r"^(col-|card-)", "", prefixed))


def test_get_board_unauthenticated(client):
    resp = client.get("/api/board")
    assert resp.status_code == 401


def test_rename_column_unauthenticated(client):
    resp = client.put("/api/columns/1", json={"title": "Hacked"})
    assert resp.status_code == 401


def test_create_card_unauthenticated(client):
    resp = client.post("/api/cards", json={"column_id": 1, "title": "Hacked"})
    assert resp.status_code == 401


def test_update_card_unauthenticated(client):
    resp = client.put("/api/cards/1", json={"title": "Hacked"})
    assert resp.status_code == 401


def test_delete_card_unauthenticated(client):
    resp = client.delete("/api/cards/1")
    assert resp.status_code == 401


def test_reorder_unauthenticated(client):
    resp = client.put("/api/board/reorder", json={"card_id": 1, "target_column_id": 2, "target_position": 0})
    assert resp.status_code == 401


def test_get_board_returns_seeded_data(authed_client):
    resp = authed_client.get("/api/board")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["columns"]) == 5
    assert data["columns"][0]["title"] == "Backlog"
    assert len(data["cards"]) == 8
    # Verify prefixed IDs
    assert data["columns"][0]["id"].startswith("col-")
    assert list(data["cards"].keys())[0].startswith("card-")


def test_rename_column(authed_client):
    board = authed_client.get("/api/board").json()
    col_id = db_id(board["columns"][0]["id"])
    resp = authed_client.put(f"/api/columns/{col_id}", json={"title": "Todo"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Todo"

    board = authed_client.get("/api/board").json()
    assert board["columns"][0]["title"] == "Todo"


def test_create_card(authed_client):
    board = authed_client.get("/api/board").json()
    col_id = db_id(board["columns"][1]["id"])
    resp = authed_client.post("/api/cards", json={"column_id": col_id, "title": "New card", "details": "Some details"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New card"

    board = authed_client.get("/api/board").json()
    assert any(c["title"] == "New card" for c in board["cards"].values())


def test_update_card(authed_client):
    board = authed_client.get("/api/board").json()
    card_id = db_id(list(board["cards"].keys())[0])
    resp = authed_client.put(f"/api/cards/{card_id}", json={"title": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


def test_delete_card(authed_client):
    board = authed_client.get("/api/board").json()
    card_key = list(board["cards"].keys())[0]
    card_id = db_id(card_key)
    resp = authed_client.delete(f"/api/cards/{card_id}")
    assert resp.status_code == 200

    board = authed_client.get("/api/board").json()
    assert card_key not in board["cards"]
    assert len(board["cards"]) == 7


def test_reorder_within_column(authed_client):
    board = authed_client.get("/api/board").json()
    col = board["columns"][0]  # Backlog has 2 cards
    first_card_id = col["cardIds"][0]
    resp = authed_client.put("/api/board/reorder", json={
        "card_id": db_id(first_card_id),
        "target_column_id": db_id(col["id"]),
        "target_position": 1,
    })
    assert resp.status_code == 200

    board = authed_client.get("/api/board").json()
    assert board["columns"][0]["cardIds"][1] == first_card_id


def test_reorder_between_columns(authed_client):
    board = authed_client.get("/api/board").json()
    src_col = board["columns"][0]  # Backlog
    dst_col = board["columns"][1]  # Discovery
    card_id = src_col["cardIds"][0]

    resp = authed_client.put("/api/board/reorder", json={
        "card_id": db_id(card_id),
        "target_column_id": db_id(dst_col["id"]),
        "target_position": 0,
    })
    assert resp.status_code == 200

    board = authed_client.get("/api/board").json()
    assert card_id in board["columns"][1]["cardIds"]
    assert card_id not in board["columns"][0]["cardIds"]
