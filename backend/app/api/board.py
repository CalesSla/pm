from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel

from app.api.auth import get_current_user_id
from app.db import get_connection

router = APIRouter()


def _require_auth(session: str) -> tuple[int, Response | None]:
    user_id = get_current_user_id(session)
    if not user_id:
        return 0, Response(
            content='{"error":"Not authenticated"}',
            status_code=401,
            media_type="application/json",
        )
    return user_id, None


def _get_board_id(user_id: int) -> int | None:
    conn = get_connection()
    row = conn.execute("SELECT id FROM boards WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row["id"] if row else None


@router.get("/board")
def get_board(session: str = Cookie(default="")):
    user_id, err = _require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    if not board_id:
        return {"columns": [], "cards": {}}

    conn = get_connection()
    columns = conn.execute(
        "SELECT id, title, position FROM columns_ WHERE board_id = ? ORDER BY position",
        (board_id,),
    ).fetchall()

    cards = conn.execute(
        """SELECT c.id, c.column_id, c.title, c.details, c.position
           FROM cards c
           JOIN columns_ col ON c.column_id = col.id
           WHERE col.board_id = ?
           ORDER BY c.position""",
        (board_id,),
    ).fetchall()
    conn.close()

    cards_by_column: dict[int, list] = {}
    cards_map = {}
    for card in cards:
        card_id = f"card-{card['id']}"
        cards_map[card_id] = {
            "id": card_id,
            "title": card["title"],
            "details": card["details"],
        }
        col_id = card["column_id"]
        cards_by_column.setdefault(col_id, []).append(card_id)

    result_columns = []
    for col in columns:
        result_columns.append({
            "id": f"col-{col['id']}",
            "title": col["title"],
            "cardIds": cards_by_column.get(col["id"], []),
        })

    return {"columns": result_columns, "cards": cards_map}


class RenameColumnRequest(BaseModel):
    title: str


@router.put("/columns/{column_id}")
def rename_column(column_id: int, body: RenameColumnRequest, session: str = Cookie(default="")):
    user_id, err = _require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    conn = get_connection()
    col = conn.execute(
        "SELECT id FROM columns_ WHERE id = ? AND board_id = ?", (column_id, board_id)
    ).fetchone()
    if not col:
        conn.close()
        return Response(content='{"error":"Column not found"}', status_code=404, media_type="application/json")

    conn.execute("UPDATE columns_ SET title = ? WHERE id = ?", (body.title, column_id))
    conn.commit()
    conn.close()
    return {"id": str(column_id), "title": body.title}


class CreateCardRequest(BaseModel):
    column_id: int
    title: str
    details: str = ""


@router.post("/cards")
def create_card(body: CreateCardRequest, session: str = Cookie(default="")):
    user_id, err = _require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    conn = get_connection()
    col = conn.execute(
        "SELECT id FROM columns_ WHERE id = ? AND board_id = ?", (body.column_id, board_id)
    ).fetchone()
    if not col:
        conn.close()
        return Response(content='{"error":"Column not found"}', status_code=404, media_type="application/json")

    position = conn.execute(
        "SELECT COUNT(*) as cnt FROM cards WHERE column_id = ?", (body.column_id,)
    ).fetchone()["cnt"]

    conn.execute(
        "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
        (body.column_id, body.title, body.details or "", position),
    )
    conn.commit()
    card_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
    conn.close()

    return {"id": str(card_id), "title": body.title, "details": body.details or ""}


class UpdateCardRequest(BaseModel):
    title: str | None = None
    details: str | None = None


@router.put("/cards/{card_id}")
def update_card(card_id: int, body: UpdateCardRequest, session: str = Cookie(default="")):
    user_id, err = _require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    conn = get_connection()
    card = conn.execute(
        """SELECT c.id, c.title, c.details FROM cards c
           JOIN columns_ col ON c.column_id = col.id
           WHERE c.id = ? AND col.board_id = ?""",
        (card_id, board_id),
    ).fetchone()
    if not card:
        conn.close()
        return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

    title = body.title if body.title is not None else card["title"]
    details = body.details if body.details is not None else card["details"]
    conn.execute("UPDATE cards SET title = ?, details = ? WHERE id = ?", (title, details, card_id))
    conn.commit()
    conn.close()

    return {"id": str(card_id), "title": title, "details": details}


@router.delete("/cards/{card_id}")
def delete_card(card_id: int, session: str = Cookie(default="")):
    user_id, err = _require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    conn = get_connection()
    card = conn.execute(
        """SELECT c.id, c.column_id, c.position FROM cards c
           JOIN columns_ col ON c.column_id = col.id
           WHERE c.id = ? AND col.board_id = ?""",
        (card_id, board_id),
    ).fetchone()
    if not card:
        conn.close()
        return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

    conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.execute(
        "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
        (card["column_id"], card["position"]),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


class ReorderRequest(BaseModel):
    card_id: int
    target_column_id: int
    target_position: int


@router.put("/board/reorder")
def reorder(body: ReorderRequest, session: str = Cookie(default="")):
    user_id, err = _require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    conn = get_connection()

    card = conn.execute(
        """SELECT c.id, c.column_id, c.position FROM cards c
           JOIN columns_ col ON c.column_id = col.id
           WHERE c.id = ? AND col.board_id = ?""",
        (body.card_id, board_id),
    ).fetchone()
    if not card:
        conn.close()
        return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

    target_col = conn.execute(
        "SELECT id FROM columns_ WHERE id = ? AND board_id = ?", (body.target_column_id, board_id)
    ).fetchone()
    if not target_col:
        conn.close()
        return Response(content='{"error":"Column not found"}', status_code=404, media_type="application/json")

    old_col_id = card["column_id"]
    old_pos = card["position"]

    if old_col_id == body.target_column_id:
        # Same column reorder
        if old_pos < body.target_position:
            conn.execute(
                "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ? AND position <= ?",
                (old_col_id, old_pos, body.target_position),
            )
        elif old_pos > body.target_position:
            conn.execute(
                "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ? AND position < ?",
                (old_col_id, body.target_position, old_pos),
            )
        conn.execute("UPDATE cards SET position = ? WHERE id = ?", (body.target_position, body.card_id))
    else:
        # Remove from old column
        conn.execute(
            "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
            (old_col_id, old_pos),
        )
        # Make room in new column
        conn.execute(
            "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
            (body.target_column_id, body.target_position),
        )
        # Move card
        conn.execute(
            "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
            (body.target_column_id, body.target_position, body.card_id),
        )

    conn.commit()
    conn.close()
    return {"ok": True}
