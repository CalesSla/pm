from fastapi import APIRouter, Cookie, Response

from app.ai.client import MODEL, get_ai_client
from app.api.auth import get_current_user_id

router = APIRouter(prefix="/ai")


def _require_auth(session: str) -> tuple[int, Response | None]:
    user_id = get_current_user_id(session)
    if not user_id:
        return 0, Response(
            content='{"error":"Not authenticated"}',
            status_code=401,
            media_type="application/json",
        )
    return user_id, None


@router.get("/test")
def ai_test(session: str = Cookie(default="")):
    _, err = _require_auth(session)
    if err:
        return err

    client = get_ai_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "What is 2+2?"}],
    )
    return {"response": response.choices[0].message.content}
