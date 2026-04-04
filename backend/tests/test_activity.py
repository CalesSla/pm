def test_activity_log_on_card_create(authed_client):
    # Get board
    board = authed_client.get("/api/board").json()
    col_id = int(board["columns"][0]["id"].replace("col-", ""))
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]

    # Create a card
    authed_client.post("/api/cards", json={"column_id": col_id, "title": "Activity test card"})

    # Check activity
    res = authed_client.get(f"/api/boards/{board_id}/activity")
    assert res.status_code == 200
    activity = res.json()["activity"]
    assert len(activity) >= 1
    assert activity[0]["action"] == "card_created"
    assert "Activity test card" in activity[0]["detail"]


def test_activity_log_on_card_update(authed_client):
    board = authed_client.get("/api/board").json()
    card_id = int(list(board["cards"].keys())[0].replace("card-", ""))
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]

    authed_client.put(f"/api/cards/{card_id}", json={"title": "Updated title"})

    res = authed_client.get(f"/api/boards/{board_id}/activity")
    activity = res.json()["activity"]
    assert any(a["action"] == "card_updated" for a in activity)


def test_activity_log_on_card_delete(authed_client):
    board = authed_client.get("/api/board").json()
    card_id = int(list(board["cards"].keys())[0].replace("card-", ""))
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]

    authed_client.delete(f"/api/cards/{card_id}")

    res = authed_client.get(f"/api/boards/{board_id}/activity")
    activity = res.json()["activity"]
    assert any(a["action"] == "card_deleted" for a in activity)


def test_activity_empty_board(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    res = authed_client.get(f"/api/boards/{board_id}/activity")
    assert res.status_code == 200
    assert res.json()["activity"] == []


def test_activity_unauthenticated(client):
    res = client.get("/api/boards/1/activity")
    assert res.status_code == 401
