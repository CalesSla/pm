import re


def db_id(prefixed: str) -> int:
    return int(re.sub(r"^(col-|card-)", "", prefixed))


def test_create_card_with_due_date(authed_client):
    board = authed_client.get("/api/board").json()
    col_id = db_id(board["columns"][0]["id"])
    resp = authed_client.post("/api/cards", json={
        "column_id": col_id,
        "title": "Due soon",
        "due_date": "2026-04-10",
    })
    assert resp.status_code == 200
    assert resp.json()["due_date"] == "2026-04-10"


def test_create_card_without_due_date(authed_client):
    board = authed_client.get("/api/board").json()
    col_id = db_id(board["columns"][0]["id"])
    resp = authed_client.post("/api/cards", json={
        "column_id": col_id,
        "title": "No deadline",
    })
    assert resp.status_code == 200
    assert resp.json()["due_date"] is None


def test_update_card_due_date(authed_client):
    board = authed_client.get("/api/board").json()
    card_id = db_id(list(board["cards"].keys())[0])
    resp = authed_client.put(f"/api/cards/{card_id}", json={"due_date": "2026-05-01"})
    assert resp.status_code == 200
    assert resp.json()["due_date"] == "2026-05-01"


def test_clear_card_due_date(authed_client):
    board = authed_client.get("/api/board").json()
    col_id = db_id(board["columns"][0]["id"])
    # Create with due date
    card = authed_client.post("/api/cards", json={
        "column_id": col_id,
        "title": "Has date",
        "due_date": "2026-04-10",
    }).json()
    card_id = int(card["id"])

    # Update to remove due date — send empty string to clear
    # Note: None means "don't change", so we explicitly clear
    resp = authed_client.put(f"/api/cards/{card_id}", json={"due_date": ""})
    assert resp.status_code == 200
    assert resp.json()["due_date"] == ""


def test_due_date_in_board_response(authed_client):
    board = authed_client.get("/api/board").json()
    col_id = db_id(board["columns"][0]["id"])
    authed_client.post("/api/cards", json={
        "column_id": col_id,
        "title": "Deadline card",
        "due_date": "2026-04-15",
    })

    board = authed_client.get("/api/board").json()
    dated_cards = [c for c in board["cards"].values() if c.get("due_date") == "2026-04-15"]
    assert len(dated_cards) == 1
    assert dated_cards[0]["title"] == "Deadline card"


def test_seeded_cards_have_no_due_date(authed_client):
    board = authed_client.get("/api/board").json()
    for card in board["cards"].values():
        assert card["due_date"] is None
