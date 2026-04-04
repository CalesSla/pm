import re


def db_id(prefixed: str) -> int:
    return int(re.sub(r"^(col-|card-)", "", prefixed))


def _get_card_id(authed_client) -> int:
    boards = authed_client.get("/api/boards").json()["boards"]
    board = authed_client.get(f"/api/boards/{boards[0]['id']}").json()
    return db_id(board["columns"][0]["cardIds"][0])


def test_create_checklist_item(authed_client):
    card_id = _get_card_id(authed_client)
    resp = authed_client.post(f"/api/cards/{card_id}/checklist", json={"title": "Sub-task 1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Sub-task 1"
    assert data["checked"] is False
    assert data["position"] == 0
    assert "id" in data


def test_list_checklist_items(authed_client):
    card_id = _get_card_id(authed_client)
    authed_client.post(f"/api/cards/{card_id}/checklist", json={"title": "Item A"})
    authed_client.post(f"/api/cards/{card_id}/checklist", json={"title": "Item B"})

    resp = authed_client.get(f"/api/cards/{card_id}/checklist")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 2
    assert items[0]["title"] == "Item A"
    assert items[1]["title"] == "Item B"
    assert items[0]["position"] == 0
    assert items[1]["position"] == 1


def test_toggle_checklist_item(authed_client):
    card_id = _get_card_id(authed_client)
    item = authed_client.post(f"/api/cards/{card_id}/checklist", json={"title": "Toggle me"}).json()

    resp = authed_client.put(f"/api/checklist/{item['id']}", json={"checked": True})
    assert resp.status_code == 200
    assert resp.json()["checked"] is True

    resp = authed_client.put(f"/api/checklist/{item['id']}", json={"checked": False})
    assert resp.json()["checked"] is False


def test_update_checklist_item_title(authed_client):
    card_id = _get_card_id(authed_client)
    item = authed_client.post(f"/api/cards/{card_id}/checklist", json={"title": "Old title"}).json()

    resp = authed_client.put(f"/api/checklist/{item['id']}", json={"title": "New title"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New title"


def test_delete_checklist_item(authed_client):
    card_id = _get_card_id(authed_client)
    item = authed_client.post(f"/api/cards/{card_id}/checklist", json={"title": "Delete me"}).json()

    resp = authed_client.delete(f"/api/checklist/{item['id']}")
    assert resp.status_code == 200

    items = authed_client.get(f"/api/cards/{card_id}/checklist").json()["items"]
    assert all(i["id"] != item["id"] for i in items)


def test_empty_title_rejected(authed_client):
    card_id = _get_card_id(authed_client)
    resp = authed_client.post(f"/api/cards/{card_id}/checklist", json={"title": "  "})
    assert resp.status_code == 400


def test_checklist_progress_in_board_response(authed_client):
    card_id = _get_card_id(authed_client)
    authed_client.post(f"/api/cards/{card_id}/checklist", json={"title": "A"})
    item_b = authed_client.post(f"/api/cards/{card_id}/checklist", json={"title": "B"}).json()
    authed_client.put(f"/api/checklist/{item_b['id']}", json={"checked": True})

    boards = authed_client.get("/api/boards").json()["boards"]
    board = authed_client.get(f"/api/boards/{boards[0]['id']}").json()
    card_data = board["cards"][f"card-{card_id}"]
    assert card_data["checklist_total"] == 2
    assert card_data["checklist_done"] == 1


def test_unauthenticated_checklist_access(client):
    resp = client.get("/api/cards/1/checklist")
    assert resp.status_code == 401

    resp = client.post("/api/cards/1/checklist", json={"title": "Test"})
    assert resp.status_code == 401

    resp = client.put("/api/checklist/1", json={"checked": True})
    assert resp.status_code == 401

    resp = client.delete("/api/checklist/1")
    assert resp.status_code == 401
