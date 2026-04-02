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
