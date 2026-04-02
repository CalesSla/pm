import secrets

from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel

router = APIRouter(prefix="/auth")

# In-memory session store: token -> username
sessions: dict[str, str] = {}

VALID_USERNAME = "user"
VALID_PASSWORD = "password"


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginRequest, response: Response):
    if body.username != VALID_USERNAME or body.password != VALID_PASSWORD:
        return Response(
            content='{"error":"Invalid credentials"}',
            status_code=401,
            media_type="application/json",
        )
    token = secrets.token_hex(32)
    sessions[token] = body.username
    response.set_cookie(key="session", value=token, httponly=True, samesite="lax")
    return {"username": body.username}


@router.post("/logout")
def logout(response: Response, session: str = Cookie(default="")):
    sessions.pop(session, None)
    response.delete_cookie("session")
    return {"ok": True}


@router.get("/me")
def me(session: str = Cookie(default="")):
    username = sessions.get(session)
    if not username:
        return Response(
            content='{"error":"Not authenticated"}',
            status_code=401,
            media_type="application/json",
        )
    return {"username": username}
