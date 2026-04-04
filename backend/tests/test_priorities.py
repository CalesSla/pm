import re


def db_id(prefixed: str) -> int:
    return int(re.sub(r"^(col-|card-)", "", prefixed))


def _get_board_data(authed_client):
    boards = authed_client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]
    board = authed_client.get(f"/api/boards/{board_id}").json()
    col_id = db_id(board["columns"][0]["id"])
    return board_id, col_id, board


def test_default_priority_is_none(authed_client):
    board_id, col_id, board = _get_board_data(authed_client)
    card_key = board["columns"][0]["cardIds"][0]
    assert board["cards"][card_key]["priority"] == "none"


def test_create_card_with_priority(authed_client):
    board_id, col_id, _ = _get_board_data(authed_client)
    resp = authed_client.post("/api/cards", json={
        "column_id": col_id,
        "title": "Urgent task",
        "priority": "urgent",
    })
    assert resp.status_code == 200
    assert resp.json()["priority"] == "urgent"


def test_update_card_priority(authed_client):
    board_id, col_id, board = _get_board_data(authed_client)
    card_id = db_id(board["columns"][0]["cardIds"][0])

    resp = authed_client.put(f"/api/cards/{card_id}", json={"priority": "high"})
    assert resp.status_code == 200
    assert resp.json()["priority"] == "high"


def test_priority_in_board_response(authed_client):
    board_id, col_id, _ = _get_board_data(authed_client)
    card = authed_client.post("/api/cards", json={
        "column_id": col_id,
        "title": "Medium task",
        "priority": "medium",
    }).json()

    board = authed_client.get(f"/api/boards/{board_id}").json()
    card_key = f"card-{card['id']}"
    assert board["cards"][card_key]["priority"] == "medium"


def test_invalid_priority_defaults_to_none(authed_client):
    _, col_id, _ = _get_board_data(authed_client)
    resp = authed_client.post("/api/cards", json={
        "column_id": col_id,
        "title": "Bad priority",
        "priority": "invalid",
    })
    assert resp.status_code == 200
    assert resp.json()["priority"] == "none"


def test_invalid_priority_on_update_keeps_old(authed_client):
    _, col_id, board = _get_board_data(authed_client)
    card = authed_client.post("/api/cards", json={
        "column_id": col_id,
        "title": "Test",
        "priority": "high",
    }).json()
    card_id = int(card["id"])

    resp = authed_client.put(f"/api/cards/{card_id}", json={"priority": "bogus"})
    assert resp.json()["priority"] == "high"
