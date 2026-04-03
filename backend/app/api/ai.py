import json

from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel

from app.ai.actions import apply_actions
from app.ai.client import ACTIONS_SCHEMA, MODEL, get_ai_client
from app.api.auth import require_auth
from app.api.board import _get_board_id, get_board
from app.db import get_db

router = APIRouter(prefix="/ai")


def _get_board_state(board_id: int) -> dict:
    """Get the board state as a plain dict for the AI system prompt."""
    with get_db() as conn:
        columns = conn.execute(
            "SELECT id, title, position FROM columns_ WHERE board_id = ? ORDER BY position",
            (board_id,),
        ).fetchall()

        result = []
        for col in columns:
            cards = conn.execute(
                "SELECT id, title, details, position FROM cards WHERE column_id = ? ORDER BY position",
                (col["id"],),
            ).fetchall()
            result.append({
                "column_id": col["id"],
                "title": col["title"],
                "position": col["position"],
                "cards": [
                    {"card_id": c["id"], "title": c["title"], "details": c["details"], "position": c["position"]}
                    for c in cards
                ],
            })
    return {"columns": result}


SYSTEM_PROMPT_TEMPLATE = """You are an AI assistant for a Kanban board project management app.
You can help the user manage their board by creating, updating, deleting, and moving cards.

Current board state:
{board_state}

When the user asks you to make changes to the board, respond with the appropriate actions.
Available action types:
- create_card: Create a new card. Requires column_id and title. details is optional.
- update_card: Update an existing card. Requires card_id. title and details are optional (only set what changes).
- delete_card: Delete a card. Requires card_id.
- move_card: Move a card to a different column or position. Requires card_id, column_id (target), and position.

Always include a helpful message explaining what you did or answering the user's question.
If the user is just chatting and not asking for board changes, respond with an empty actions list.
Use the actual database IDs (integers) from the board state above for column_id and card_id."""


@router.get("/test")
def ai_test(session: str = Cookie(default="")):
    _, err = require_auth(session)
    if err:
        return err

    client = get_ai_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "What is 2+2?"}],
    )
    return {"response": response.choices[0].message.content}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


@router.post("/chat")
def ai_chat(body: ChatRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    if not board_id:
        return Response(
            content='{"error":"No board found"}',
            status_code=404,
            media_type="application/json",
        )

    board_state = _get_board_state(board_id)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(board_state=json.dumps(board_state, indent=2))

    messages = [{"role": "system", "content": system_prompt}]
    for msg in body.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": body.message})

    client = get_ai_client()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format=ACTIONS_SCHEMA,
        )
        if not response.choices:
            return Response(
                content='{"error":"AI returned no response"}',
                status_code=502,
                media_type="application/json",
            )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return Response(
            content='{"error":"AI returned invalid response format"}',
            status_code=502,
            media_type="application/json",
        )
    except Exception:
        return Response(
            content='{"error":"Failed to get AI response"}',
            status_code=502,
            media_type="application/json",
        )

    ai_message = parsed.get("message", "")
    actions = parsed.get("actions", [])

    action_results = []
    if actions:
        action_results = apply_actions(actions, board_id)

    # Return updated board state
    updated_board = get_board(session)

    return {
        "message": ai_message,
        "actions": actions,
        "action_results": action_results,
        "board": updated_board,
    }
