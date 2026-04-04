import re


def db_id(prefixed: str) -> int:
    return int(re.sub(r"^(col-|card-)", "", prefixed))


def _get_card_id(authed_client) -> int:
    boards = authed_client.get("/api/boards").json()["boards"]
    board = authed_client.get(f"/api/boards/{boards[0]['id']}").json()
    return db_id(board["columns"][0]["cardIds"][0])


def test_create_comment(authed_client):
    card_id = _get_card_id(authed_client)
    resp = authed_client.post(f"/api/cards/{card_id}/comments", json={"content": "This looks good"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "This looks good"
    assert data["user"]["username"] == "user"
    assert "id" in data


def test_list_comments(authed_client):
    card_id = _get_card_id(authed_client)
    authed_client.post(f"/api/cards/{card_id}/comments", json={"content": "Comment 1"})
    authed_client.post(f"/api/cards/{card_id}/comments", json={"content": "Comment 2"})

    resp = authed_client.get(f"/api/cards/{card_id}/comments")
    assert resp.status_code == 200
    comments = resp.json()["comments"]
    assert len(comments) == 2
    assert comments[0]["content"] == "Comment 1"
    assert comments[1]["content"] == "Comment 2"


def test_delete_comment(authed_client):
    card_id = _get_card_id(authed_client)
    comment = authed_client.post(f"/api/cards/{card_id}/comments", json={"content": "Temp"}).json()

    resp = authed_client.delete(f"/api/comments/{comment['id']}")
    assert resp.status_code == 200

    comments = authed_client.get(f"/api/cards/{card_id}/comments").json()["comments"]
    assert len(comments) == 0


def test_empty_comment_rejected(authed_client):
    card_id = _get_card_id(authed_client)
    resp = authed_client.post(f"/api/cards/{card_id}/comments", json={"content": "  "})
    assert resp.status_code == 400


def test_comment_count_in_board_response(authed_client):
    card_id = _get_card_id(authed_client)
    authed_client.post(f"/api/cards/{card_id}/comments", json={"content": "One"})
    authed_client.post(f"/api/cards/{card_id}/comments", json={"content": "Two"})

    boards = authed_client.get("/api/boards").json()["boards"]
    board = authed_client.get(f"/api/boards/{boards[0]['id']}").json()
    card_key = f"card-{card_id}"
    assert board["cards"][card_key]["comment_count"] == 2


def test_delete_other_user_comment_fails(authed_client):
    card_id = _get_card_id(authed_client)
    comment = authed_client.post(f"/api/cards/{card_id}/comments", json={"content": "Mine"}).json()

    # Register and log in as another user
    from fastapi.testclient import TestClient
    from app.main import app
    other = TestClient(app)
    other.post("/api/auth/register", json={"username": "other", "password": "pass1234"})
    resp = other.delete(f"/api/comments/{comment['id']}")
    assert resp.status_code == 404


def test_comments_unauthenticated(client):
    resp = client.get("/api/cards/1/comments")
    assert resp.status_code == 401

    resp = client.post("/api/cards/1/comments", json={"content": "test"})
    assert resp.status_code == 401

    resp = client.delete("/api/comments/1")
    assert resp.status_code == 401


def test_comments_deleted_on_card_delete(authed_client):
    card_id = _get_card_id(authed_client)
    authed_client.post(f"/api/cards/{card_id}/comments", json={"content": "Will be gone"})

    authed_client.delete(f"/api/cards/{card_id}")

    resp = authed_client.get(f"/api/cards/{card_id}/comments")
    assert resp.status_code == 404
