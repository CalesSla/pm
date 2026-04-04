def test_board_stats(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    res = authed_client.get(f"/api/boards/{board_id}/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_cards"] == 8  # seed cards
    assert data["member_count"] == 1  # owner only
    assert len(data["columns"]) == 5  # default columns
    # Verify column card counts sum to total
    assert sum(c["card_count"] for c in data["columns"]) == data["total_cards"]


def test_board_stats_after_card_create(authed_client):
    board = authed_client.get("/api/board").json()
    col_id = int(board["columns"][0]["id"].replace("col-", ""))
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]

    authed_client.post("/api/cards", json={"column_id": col_id, "title": "New card"})

    res = authed_client.get(f"/api/boards/{board_id}/stats")
    assert res.json()["total_cards"] == 9


def test_board_stats_unauthenticated(client):
    res = client.get("/api/boards/1/stats")
    assert res.status_code == 401


def test_board_stats_not_found(authed_client):
    res = authed_client.get("/api/boards/9999/stats")
    assert res.status_code == 404
