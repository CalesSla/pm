import json
from unittest.mock import MagicMock, patch

from app.ai.client import get_ai_client


def test_ai_client_initializes():
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
        client = get_ai_client()
        assert client.base_url == "https://openrouter.ai/api/v1/"
        assert client.api_key == "test-key"


def test_ai_test_requires_auth(client):
    resp = client.get("/api/ai/test")
    assert resp.status_code == 401


def test_ai_test_returns_response(authed_client):
    mock_message = MagicMock()
    mock_message.content = "4"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("app.api.ai.get_ai_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get.return_value = mock_client

        resp = authed_client.get("/api/ai/test")
        assert resp.status_code == 200
        assert resp.json()["response"] == "4"

        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "openai/gpt-oss-120b"


# --- /api/ai/chat tests ---


def _mock_ai_response(message: str, actions: list[dict] | None = None):
    """Create a mock OpenAI response with structured output."""
    content = json.dumps({"message": message, "actions": actions or []})
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


def _get_column_ids(authed_client) -> list[int]:
    """Get the real DB column IDs from the board."""
    resp = authed_client.get("/api/board")
    columns = resp.json()["columns"]
    return [int(c["id"].replace("col-", "")) for c in columns]


def _get_card_ids(authed_client) -> list[int]:
    """Get all real DB card IDs from the board."""
    resp = authed_client.get("/api/board")
    cards = resp.json()["cards"]
    return [int(cid.replace("card-", "")) for cid in cards]


def test_chat_requires_auth(client):
    resp = client.post("/api/ai/chat", json={"message": "hello"})
    assert resp.status_code == 401


def test_chat_no_actions(authed_client):
    mock_resp = _mock_ai_response("Hello! How can I help with your board?")

    with patch("app.api.ai.get_ai_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get.return_value = mock_client

        resp = authed_client.post("/api/ai/chat", json={"message": "hello"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Hello! How can I help with your board?"
        assert data["actions"] == []
        assert data["action_results"] == []
        assert "board" in data


def test_chat_create_card(authed_client):
    col_ids = _get_column_ids(authed_client)
    mock_resp = _mock_ai_response("Created a new card!", [
        {"type": "create_card", "column_id": col_ids[0], "card_id": None, "title": "AI Card", "details": "Made by AI", "position": None},
    ])

    with patch("app.api.ai.get_ai_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get.return_value = mock_client

        resp = authed_client.post("/api/ai/chat", json={"message": "create a card"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Created a new card!"
        assert len(data["actions"]) == 1
        assert data["action_results"][0]["ok"] is True

        # Verify card exists on the board
        board = data["board"]
        card_titles = [c["title"] for c in board["cards"].values()]
        assert "AI Card" in card_titles


def test_chat_update_card(authed_client):
    card_ids = _get_card_ids(authed_client)
    mock_resp = _mock_ai_response("Updated the card.", [
        {"type": "update_card", "column_id": None, "card_id": card_ids[0], "title": "Updated Title", "details": None, "position": None},
    ])

    with patch("app.api.ai.get_ai_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get.return_value = mock_client

        resp = authed_client.post("/api/ai/chat", json={"message": "update a card"})
        data = resp.json()
        assert data["action_results"][0]["ok"] is True

        board = data["board"]
        updated = board["cards"][f"card-{card_ids[0]}"]
        assert updated["title"] == "Updated Title"


def test_chat_delete_card(authed_client):
    card_ids = _get_card_ids(authed_client)
    target_id = card_ids[0]
    mock_resp = _mock_ai_response("Deleted the card.", [
        {"type": "delete_card", "column_id": None, "card_id": target_id, "title": None, "details": None, "position": None},
    ])

    with patch("app.api.ai.get_ai_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get.return_value = mock_client

        resp = authed_client.post("/api/ai/chat", json={"message": "delete a card"})
        data = resp.json()
        assert data["action_results"][0]["ok"] is True
        assert f"card-{target_id}" not in data["board"]["cards"]


def test_chat_move_card(authed_client):
    col_ids = _get_column_ids(authed_client)
    card_ids = _get_card_ids(authed_client)

    # Move first card to last column, position 0
    mock_resp = _mock_ai_response("Moved the card.", [
        {"type": "move_card", "column_id": col_ids[-1], "card_id": card_ids[0], "title": None, "details": None, "position": 0},
    ])

    with patch("app.api.ai.get_ai_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get.return_value = mock_client

        resp = authed_client.post("/api/ai/chat", json={"message": "move a card"})
        data = resp.json()
        assert data["action_results"][0]["ok"] is True


def test_chat_multiple_actions(authed_client):
    col_ids = _get_column_ids(authed_client)
    card_ids = _get_card_ids(authed_client)

    mock_resp = _mock_ai_response("Done! Created one card and deleted another.", [
        {"type": "create_card", "column_id": col_ids[0], "card_id": None, "title": "New Card", "details": "", "position": None},
        {"type": "delete_card", "column_id": None, "card_id": card_ids[0], "title": None, "details": None, "position": None},
    ])

    with patch("app.api.ai.get_ai_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get.return_value = mock_client

        resp = authed_client.post("/api/ai/chat", json={"message": "create and delete"})
        data = resp.json()
        assert len(data["actions"]) == 2
        assert all(r["ok"] for r in data["action_results"])


def test_chat_invalid_action_type(authed_client):
    mock_resp = _mock_ai_response("Trying something weird.", [
        {"type": "explode_board", "column_id": None, "card_id": None, "title": None, "details": None, "position": None},
    ])

    with patch("app.api.ai.get_ai_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get.return_value = mock_client

        resp = authed_client.post("/api/ai/chat", json={"message": "do something"})
        data = resp.json()
        assert data["action_results"][0]["ok"] is False


def test_chat_with_history(authed_client):
    mock_resp = _mock_ai_response("Sure, based on our conversation...")

    with patch("app.api.ai.get_ai_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get.return_value = mock_client

        resp = authed_client.post("/api/ai/chat", json={
            "message": "what did I just say?",
            "history": [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        })
        assert resp.status_code == 200

        # Verify history was passed to the AI
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[1] == {"role": "user", "content": "hello"}
        assert messages[2] == {"role": "assistant", "content": "Hi there!"}
        assert messages[3] == {"role": "user", "content": "what did I just say?"}
