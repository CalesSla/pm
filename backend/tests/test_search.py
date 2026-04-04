def test_search_cards_by_title(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    resp = authed_client.get(f"/api/boards/{board_id}/search?q=roadmap")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["title"] == "Align roadmap themes"


def test_search_cards_by_details(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    resp = authed_client.get(f"/api/boards/{board_id}/search?q=dashboard")
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["title"] == "Prototype analytics view"


def test_search_case_insensitive(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    resp = authed_client.get(f"/api/boards/{board_id}/search?q=ROADMAP")
    assert len(resp.json()["results"]) == 1


def test_search_no_results(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    resp = authed_client.get(f"/api/boards/{board_id}/search?q=nonexistent")
    assert resp.json()["results"] == []


def test_search_empty_query(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    resp = authed_client.get(f"/api/boards/{board_id}/search?q=")
    assert resp.json()["results"] == []


def test_search_returns_column_info(authed_client):
    board_id = authed_client.get("/api/boards").json()["boards"][0]["id"]
    resp = authed_client.get(f"/api/boards/{board_id}/search?q=roadmap")
    result = resp.json()["results"][0]
    assert result["column_title"] == "Backlog"
    assert result["column_id"].startswith("col-")


def test_search_unauthenticated(client):
    resp = client.get("/api/boards/1/search?q=test")
    assert resp.status_code == 401


def test_search_wrong_board(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "pass1"})
    boards = client.get("/api/boards").json()["boards"]
    alice_board_id = boards[0]["id"]
    client.post("/api/auth/logout")

    client.post("/api/auth/register", json={"username": "bob", "password": "pass2"})
    resp = client.get(f"/api/boards/{alice_board_id}/search?q=test")
    assert resp.status_code == 404
