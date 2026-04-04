import re


def db_id(prefixed: str) -> int:
    return int(re.sub(r"^(col-|card-)", "", prefixed))


def _get_board_and_card(authed_client) -> tuple[int, int, int]:
    """Returns (board_id, column_db_id, card_db_id) from seeded data."""
    boards = authed_client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]
    board = authed_client.get(f"/api/boards/{board_id}").json()
    col_id = db_id(board["columns"][0]["id"])
    card_id = db_id(board["columns"][0]["cardIds"][0])
    return board_id, col_id, card_id


def test_create_label(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    resp = authed_client.post("/api/labels", json={
        "board_id": board_id,
        "name": "Bug",
        "color": "#ef4444",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Bug"
    assert data["color"] == "#ef4444"
    assert "id" in data


def test_create_label_default_color(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    resp = authed_client.post("/api/labels", json={"board_id": board_id, "name": "Feature"})
    assert resp.json()["color"] == "#6b7280"


def test_delete_label(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    label = authed_client.post("/api/labels", json={"board_id": board_id, "name": "Temp"}).json()
    resp = authed_client.delete(f"/api/labels/{label['id']}")
    assert resp.status_code == 200


def test_labels_appear_in_board_response(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    authed_client.post("/api/labels", json={"board_id": board_id, "name": "Urgent", "color": "#dc2626"})

    board = authed_client.get(f"/api/boards/{board_id}").json()
    assert len(board["labels"]) == 1
    assert board["labels"][0]["name"] == "Urgent"


def test_add_label_to_card(authed_client):
    board_id, col_id, card_id = _get_board_and_card(authed_client)
    label = authed_client.post("/api/labels", json={"board_id": board_id, "name": "Bug"}).json()

    resp = authed_client.post("/api/cards/labels", json={"card_id": card_id, "label_id": label["id"]})
    assert resp.status_code == 200

    board = authed_client.get(f"/api/boards/{board_id}").json()
    card_key = f"card-{card_id}"
    assert len(board["cards"][card_key]["labels"]) == 1
    assert board["cards"][card_key]["labels"][0]["name"] == "Bug"


def test_add_duplicate_label_to_card(authed_client):
    board_id, col_id, card_id = _get_board_and_card(authed_client)
    label = authed_client.post("/api/labels", json={"board_id": board_id, "name": "Bug"}).json()

    authed_client.post("/api/cards/labels", json={"card_id": card_id, "label_id": label["id"]})
    resp = authed_client.post("/api/cards/labels", json={"card_id": card_id, "label_id": label["id"]})
    assert resp.status_code == 200  # Should not error

    board = authed_client.get(f"/api/boards/{board_id}").json()
    card_key = f"card-{card_id}"
    assert len(board["cards"][card_key]["labels"]) == 1


def test_remove_label_from_card(authed_client):
    board_id, col_id, card_id = _get_board_and_card(authed_client)
    label = authed_client.post("/api/labels", json={"board_id": board_id, "name": "Bug"}).json()
    authed_client.post("/api/cards/labels", json={"card_id": card_id, "label_id": label["id"]})

    resp = authed_client.delete(f"/api/cards/{card_id}/labels/{label['id']}")
    assert resp.status_code == 200

    board = authed_client.get(f"/api/boards/{board_id}").json()
    card_key = f"card-{card_id}"
    assert len(board["cards"][card_key]["labels"]) == 0


def test_delete_label_removes_from_cards(authed_client):
    board_id, col_id, card_id = _get_board_and_card(authed_client)
    label = authed_client.post("/api/labels", json={"board_id": board_id, "name": "Bug"}).json()
    authed_client.post("/api/cards/labels", json={"card_id": card_id, "label_id": label["id"]})

    authed_client.delete(f"/api/labels/{label['id']}")

    board = authed_client.get(f"/api/boards/{board_id}").json()
    card_key = f"card-{card_id}"
    assert len(board["cards"][card_key]["labels"]) == 0


def test_label_unauthenticated(client):
    resp = client.post("/api/labels", json={"board_id": 1, "name": "Bug"})
    assert resp.status_code == 401

    resp = client.delete("/api/labels/1")
    assert resp.status_code == 401

    resp = client.post("/api/cards/labels", json={"card_id": 1, "label_id": 1})
    assert resp.status_code == 401
