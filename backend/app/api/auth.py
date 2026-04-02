import secrets

import bcrypt
from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel

from app.db import get_connection

router = APIRouter(prefix="/auth")

# In-memory session store: token -> user_id
sessions: dict[str, int] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginRequest, response: Response):
    conn = get_connection()
    row = conn.execute("SELECT id, password_hash FROM users WHERE username = ?", (body.username,)).fetchone()
    conn.close()

    if not row or not bcrypt.checkpw(body.password.encode(), row["password_hash"].encode()):
        return Response(
            content='{"error":"Invalid credentials"}',
            status_code=401,
            media_type="application/json",
        )

    token = secrets.token_hex(32)
    sessions[token] = row["id"]
    response.set_cookie(key="session", value=token, httponly=True, samesite="lax")
    return {"username": body.username}


@router.post("/logout")
def logout(response: Response, session: str = Cookie(default="")):
    sessions.pop(session, None)
    response.delete_cookie("session")
    return {"ok": True}


@router.get("/me")
def me(session: str = Cookie(default="")):
    user_id = sessions.get(session)
    if not user_id:
        return Response(
            content='{"error":"Not authenticated"}',
            status_code=401,
            media_type="application/json",
        )
    conn = get_connection()
    row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return Response(
            content='{"error":"Not authenticated"}',
            status_code=401,
            media_type="application/json",
        )
    return {"username": row["username"]}


def get_current_user_id(session: str = Cookie(default="")) -> int | None:
    return sessions.get(session)
