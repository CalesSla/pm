import secrets
import time

import bcrypt
from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel

from app.db import create_board_with_columns, get_db

router = APIRouter(prefix="/auth")

SESSION_TTL = 24 * 60 * 60  # 24 hours in seconds

# In-memory session store: token -> (user_id, created_at)
sessions: dict[str, tuple[int, float]] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str = ""


@router.post("/login")
def login(body: LoginRequest, response: Response):
    with get_db() as conn:
        row = conn.execute("SELECT id, password_hash FROM users WHERE username = ?", (body.username,)).fetchone()

    if not row or not bcrypt.checkpw(body.password.encode(), row["password_hash"].encode()):
        return Response(
            content='{"error":"Invalid credentials"}',
            status_code=401,
            media_type="application/json",
        )

    token = secrets.token_hex(32)
    sessions[token] = (row["id"], time.time())
    response.set_cookie(key="session", value=token, httponly=True, samesite="lax")
    return {"username": body.username}


@router.post("/register")
def register(body: RegisterRequest, response: Response):
    if len(body.username) < 2:
        return Response(
            content='{"error":"Username must be at least 2 characters"}',
            status_code=400,
            media_type="application/json",
        )
    if len(body.password) < 4:
        return Response(
            content='{"error":"Password must be at least 4 characters"}',
            status_code=400,
            media_type="application/json",
        )

    with get_db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (body.username,)).fetchone()
        if existing:
            return Response(
                content='{"error":"Username already taken"}',
                status_code=409,
                media_type="application/json",
            )

        pw_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
        display_name = body.display_name or body.username
        conn.execute(
            "INSERT INTO users (username, display_name, password_hash) VALUES (?, ?, ?)",
            (body.username, display_name, pw_hash),
        )
        conn.commit()
        user_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]

        create_board_with_columns(conn, user_id, "My Board")

    token = secrets.token_hex(32)
    sessions[token] = (user_id, time.time())
    response.set_cookie(key="session", value=token, httponly=True, samesite="lax")
    return {"username": body.username, "display_name": display_name}


@router.post("/logout")
def logout(response: Response, session: str = Cookie(default="")):
    sessions.pop(session, None)
    response.delete_cookie("session")
    return {"ok": True}


@router.get("/me")
def me(session: str = Cookie(default="")):
    user_id = get_current_user_id(session)
    if not user_id:
        return Response(
            content='{"error":"Not authenticated"}',
            status_code=401,
            media_type="application/json",
        )
    with get_db() as conn:
        row = conn.execute("SELECT username, display_name FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return Response(
            content='{"error":"Not authenticated"}',
            status_code=401,
            media_type="application/json",
        )
    return {"username": row["username"], "display_name": row["display_name"]}


def get_current_user_id(session: str = Cookie(default="")) -> int | None:
    entry = sessions.get(session)
    if not entry:
        return None
    user_id, created_at = entry
    if time.time() - created_at > SESSION_TTL:
        sessions.pop(session, None)
        return None
    return user_id


class UpdateProfileRequest(BaseModel):
    display_name: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.put("/profile")
def update_profile(body: UpdateProfileRequest, session: str = Cookie(default="")):
    user_id = get_current_user_id(session)
    if not user_id:
        return Response(
            content='{"error":"Not authenticated"}',
            status_code=401,
            media_type="application/json",
        )
    if len(body.display_name.strip()) < 1:
        return Response(
            content='{"error":"Display name cannot be empty"}',
            status_code=400,
            media_type="application/json",
        )
    with get_db() as conn:
        conn.execute("UPDATE users SET display_name = ? WHERE id = ?", (body.display_name.strip(), user_id))
        conn.commit()
    return {"display_name": body.display_name.strip()}


@router.put("/password")
def change_password(body: ChangePasswordRequest, session: str = Cookie(default="")):
    user_id = get_current_user_id(session)
    if not user_id:
        return Response(
            content='{"error":"Not authenticated"}',
            status_code=401,
            media_type="application/json",
        )
    if len(body.new_password) < 4:
        return Response(
            content='{"error":"Password must be at least 4 characters"}',
            status_code=400,
            media_type="application/json",
        )
    with get_db() as conn:
        row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row or not bcrypt.checkpw(body.current_password.encode(), row["password_hash"].encode()):
            return Response(
                content='{"error":"Current password is incorrect"}',
                status_code=403,
                media_type="application/json",
            )
        new_hash = bcrypt.hashpw(body.new_password.encode(), bcrypt.gensalt()).decode()
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
        conn.commit()
    return {"ok": True}


def require_auth(session: str) -> tuple[int, Response | None]:
    user_id = get_current_user_id(session)
    if not user_id:
        return 0, Response(
            content='{"error":"Not authenticated"}',
            status_code=401,
            media_type="application/json",
        )
    return user_id, None
