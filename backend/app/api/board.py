from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel

from app.api.auth import require_auth
from app.db import DEFAULT_COLUMNS, create_board_with_columns, get_db

router = APIRouter()


# ── Activity logging ──────────────────────────────────────────────────


def _log_activity(conn, board_id: int, user_id: int, action: str, detail: str = "", card_id: int | None = None):
    conn.execute(
        "INSERT INTO activity_log (board_id, user_id, card_id, action, detail) VALUES (?, ?, ?, ?, ?)",
        (board_id, user_id, card_id, action, detail),
    )


# ── Board CRUD ──────────────────────────────────────────────────────


def _get_board_id(user_id: int) -> int | None:
    """Get the first board for a user (legacy helper)."""
    with get_db() as conn:
        row = conn.execute("SELECT id FROM boards WHERE user_id = ? ORDER BY id LIMIT 1", (user_id,)).fetchone()
    return row["id"] if row else None


def _verify_board_ownership(user_id: int, board_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute("SELECT id FROM boards WHERE id = ? AND user_id = ?", (board_id, user_id)).fetchone()
    return row is not None


@router.get("/boards")
def list_boards(session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        owned = conn.execute(
            "SELECT id, title, created_at FROM boards WHERE user_id = ? ORDER BY created_at",
            (user_id,),
        ).fetchall()

        shared = conn.execute(
            """SELECT b.id, b.title, b.created_at FROM boards b
               JOIN board_members bm ON bm.board_id = b.id
               WHERE bm.user_id = ?
               ORDER BY b.created_at""",
            (user_id,),
        ).fetchall()

    boards = [{"id": row["id"], "title": row["title"], "created_at": row["created_at"], "role": "owner"} for row in owned]
    boards += [{"id": row["id"], "title": row["title"], "created_at": row["created_at"], "role": "member"} for row in shared]

    return {"boards": boards}


class CreateBoardRequest(BaseModel):
    title: str = "New Board"


@router.post("/boards")
def create_board(body: CreateBoardRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        board_id = create_board_with_columns(conn, user_id, body.title)

    return {"id": board_id, "title": body.title}


class RenameBoardRequest(BaseModel):
    title: str


@router.put("/boards/{board_id}")
def rename_board(board_id: int, body: RenameBoardRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    if not _verify_board_ownership(user_id, board_id):
        return Response(content='{"error":"Board not found"}', status_code=404, media_type="application/json")

    with get_db() as conn:
        conn.execute("UPDATE boards SET title = ? WHERE id = ?", (body.title, board_id))
        conn.commit()

    return {"id": board_id, "title": body.title}


@router.get("/boards/{board_id}/stats")
def get_board_stats(board_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    if not _can_access_board(user_id, board_id):
        return Response(content='{"error":"Board not found"}', status_code=404, media_type="application/json")

    with get_db() as conn:
        columns = conn.execute(
            """SELECT col.title, COUNT(c.id) as card_count
               FROM columns_ col
               LEFT JOIN cards c ON c.column_id = col.id
               WHERE col.board_id = ?
               GROUP BY col.id
               ORDER BY col.position""",
            (board_id,),
        ).fetchall()

        total = conn.execute(
            """SELECT COUNT(*) as cnt FROM cards c
               JOIN columns_ col ON c.column_id = col.id
               WHERE col.board_id = ?""",
            (board_id,),
        ).fetchone()["cnt"]

        member_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM board_members WHERE board_id = ?",
            (board_id,),
        ).fetchone()["cnt"] + 1  # +1 for owner

    return {
        "total_cards": total,
        "member_count": member_count,
        "columns": [{"title": c["title"], "card_count": c["card_count"]} for c in columns],
    }


@router.delete("/boards/{board_id}")
def delete_board(board_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    if not _verify_board_ownership(user_id, board_id):
        return Response(content='{"error":"Board not found"}', status_code=404, media_type="application/json")

    with get_db() as conn:
        conn.execute("DELETE FROM boards WHERE id = ?", (board_id,))
        conn.commit()

    return {"ok": True}


# ── Single board data ───────────────────────────────────────────────


@router.get("/boards/{board_id}")
def get_board(board_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    # Allow owner or member to view board
    if not _verify_board_ownership(user_id, board_id):
        with get_db() as conn:
            member = conn.execute(
                "SELECT 1 FROM board_members WHERE board_id = ? AND user_id = ?", (board_id, user_id)
            ).fetchone()
        if not member:
            return Response(content='{"error":"Board not found"}', status_code=404, media_type="application/json")

    return _build_board_response(board_id)


@router.get("/board")
def get_default_board(session: str = Cookie(default="")):
    """Legacy endpoint: returns the user's first board."""
    user_id, err = require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    if not board_id:
        return {"columns": [], "cards": {}}

    return _build_board_response(board_id)


def _build_board_response(board_id: int) -> dict:
    with get_db() as conn:
        columns = conn.execute(
            "SELECT id, title, position FROM columns_ WHERE board_id = ? ORDER BY position",
            (board_id,),
        ).fetchall()

        cards = conn.execute(
            """SELECT c.id, c.column_id, c.title, c.details, c.position, c.due_date, c.priority
               FROM cards c
               JOIN columns_ col ON c.column_id = col.id
               WHERE col.board_id = ?
               ORDER BY c.position""",
            (board_id,),
        ).fetchall()

        # Fetch labels for all cards on this board
        card_labels = conn.execute(
            """SELECT cl.card_id, l.id, l.name, l.color
               FROM card_labels cl
               JOIN labels l ON cl.label_id = l.id
               JOIN cards c ON cl.card_id = c.id
               JOIN columns_ col ON c.column_id = col.id
               WHERE col.board_id = ?""",
            (board_id,),
        ).fetchall()

        # Fetch board-level labels
        board_labels = conn.execute(
            "SELECT id, name, color FROM labels WHERE board_id = ?", (board_id,)
        ).fetchall()

        # Fetch comment counts
        comment_counts = conn.execute(
            """SELECT c.id as card_id, COUNT(cm.id) as cnt
               FROM cards c
               JOIN columns_ col ON c.column_id = col.id
               LEFT JOIN comments cm ON cm.card_id = c.id
               WHERE col.board_id = ?
               GROUP BY c.id""",
            (board_id,),
        ).fetchall()

        # Fetch checklist progress (total and checked counts per card)
        checklist_progress = conn.execute(
            """SELECT ci.card_id,
                      COUNT(*) as total,
                      SUM(CASE WHEN ci.checked = 1 THEN 1 ELSE 0 END) as done
               FROM checklist_items ci
               JOIN cards c ON ci.card_id = c.id
               JOIN columns_ col ON c.column_id = col.id
               WHERE col.board_id = ?
               GROUP BY ci.card_id""",
            (board_id,),
        ).fetchall()

        # Fetch card assignments
        assignments = conn.execute(
            """SELECT ca.card_id, u.id as user_id, u.username, u.display_name
               FROM card_assignments ca
               JOIN users u ON ca.user_id = u.id
               JOIN cards c ON ca.card_id = c.id
               JOIN columns_ col ON c.column_id = col.id
               WHERE col.board_id = ?""",
            (board_id,),
        ).fetchall()

        # Fetch board members
        members = conn.execute(
            """SELECT u.id, u.username, u.display_name, bm.role
               FROM board_members bm
               JOIN users u ON bm.user_id = u.id
               WHERE bm.board_id = ?""",
            (board_id,),
        ).fetchall()

        # Get the board owner
        owner_row = conn.execute(
            """SELECT u.id, u.username, u.display_name FROM users u
               JOIN boards b ON b.user_id = u.id
               WHERE b.id = ?""",
            (board_id,),
        ).fetchone()

    labels_by_card: dict[int, list] = {}
    for cl in card_labels:
        labels_by_card.setdefault(cl["card_id"], []).append(
            {"id": cl["id"], "name": cl["name"], "color": cl["color"]}
        )

    comment_count_map: dict[int, int] = {}
    for cc in comment_counts:
        comment_count_map[cc["card_id"]] = cc["cnt"]

    checklist_map: dict[int, dict] = {}
    for cp in checklist_progress:
        checklist_map[cp["card_id"]] = {"total": cp["total"], "done": cp["done"]}

    assignments_by_card: dict[int, list] = {}
    for a in assignments:
        assignments_by_card.setdefault(a["card_id"], []).append(
            {"id": a["user_id"], "username": a["username"], "display_name": a["display_name"]}
        )

    cards_by_column: dict[int, list] = {}
    cards_map = {}
    for card in cards:
        card_id = f"card-{card['id']}"
        cards_map[card_id] = {
            "id": card_id,
            "title": card["title"],
            "details": card["details"],
            "due_date": card["due_date"],
            "priority": card["priority"],
            "labels": labels_by_card.get(card["id"], []),
            "comment_count": comment_count_map.get(card["id"], 0),
            "checklist_total": checklist_map.get(card["id"], {}).get("total", 0),
            "checklist_done": checklist_map.get(card["id"], {}).get("done", 0),
            "assignees": assignments_by_card.get(card["id"], []),
        }
        col_id = card["column_id"]
        cards_by_column.setdefault(col_id, []).append(card_id)

    result_columns = [
        {"id": f"col-{col['id']}", "title": col["title"], "cardIds": cards_by_column.get(col["id"], [])}
        for col in columns
    ]

    def _member_dict(row, role=None):
        return {"id": row["id"], "username": row["username"], "display_name": row["display_name"], "role": role or row["role"]}

    members_list = [_member_dict(owner_row, "owner")] if owner_row else []
    members_list += [_member_dict(m) for m in members]

    return {
        "columns": result_columns,
        "cards": cards_map,
        "labels": [{"id": lb["id"], "name": lb["name"], "color": lb["color"]} for lb in board_labels],
        "members": members_list,
    }


# ── Column operations ──────────────────────────────────────────────


class RenameColumnRequest(BaseModel):
    title: str


@router.put("/columns/{column_id}")
def rename_column(column_id: int, body: RenameColumnRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    with get_db() as conn:
        col = conn.execute(
            "SELECT id FROM columns_ WHERE id = ? AND board_id = ?", (column_id, board_id)
        ).fetchone()
        if not col:
            return Response(content='{"error":"Column not found"}', status_code=404, media_type="application/json")

        conn.execute("UPDATE columns_ SET title = ? WHERE id = ?", (body.title, column_id))
        conn.commit()
    return {"id": str(column_id), "title": body.title}


class CreateColumnRequest(BaseModel):
    board_id: int
    title: str


@router.post("/columns")
def create_column(body: CreateColumnRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    if not _verify_board_ownership(user_id, body.board_id):
        return Response(content='{"error":"Board not found"}', status_code=404, media_type="application/json")

    with get_db() as conn:
        position = conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 as pos FROM columns_ WHERE board_id = ?",
            (body.board_id,),
        ).fetchone()["pos"]

        conn.execute(
            "INSERT INTO columns_ (board_id, title, position) VALUES (?, ?, ?)",
            (body.board_id, body.title, position),
        )
        conn.commit()
        col_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]

    return {"id": col_id, "title": body.title, "position": position}


@router.delete("/columns/{column_id}")
def delete_column(column_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        col = conn.execute(
            """SELECT c.id, c.board_id, c.position FROM columns_ c
               JOIN boards b ON c.board_id = b.id
               WHERE c.id = ? AND b.user_id = ?""",
            (column_id, user_id),
        ).fetchone()
        if not col:
            return Response(content='{"error":"Column not found"}', status_code=404, media_type="application/json")

        conn.execute("DELETE FROM columns_ WHERE id = ?", (column_id,))
        conn.execute(
            "UPDATE columns_ SET position = position - 1 WHERE board_id = ? AND position > ?",
            (col["board_id"], col["position"]),
        )
        conn.commit()

    return {"ok": True}


# ── Search ──────────────────────────────────────────────────────────


@router.get("/boards/{board_id}/search")
def search_cards(board_id: int, q: str = "", session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    if not _verify_board_ownership(user_id, board_id):
        return Response(content='{"error":"Board not found"}', status_code=404, media_type="application/json")

    if not q.strip():
        return {"results": []}

    term = f"%{q.strip()}%"
    with get_db() as conn:
        rows = conn.execute(
            """SELECT c.id, c.title, c.details, c.due_date, col.id as column_id, col.title as column_title
               FROM cards c
               JOIN columns_ col ON c.column_id = col.id
               WHERE col.board_id = ? AND (c.title LIKE ? OR c.details LIKE ?)
               ORDER BY c.title""",
            (board_id, term, term),
        ).fetchall()

    return {
        "results": [
            {
                "id": f"card-{r['id']}",
                "title": r["title"],
                "details": r["details"],
                "due_date": r["due_date"],
                "column_id": f"col-{r['column_id']}",
                "column_title": r["column_title"],
            }
            for r in rows
        ]
    }


# ── Card operations ─────────────────────────────────────────────────


VALID_PRIORITIES = {"none", "low", "medium", "high", "urgent"}


class CreateCardRequest(BaseModel):
    column_id: int
    title: str
    details: str = ""
    due_date: str | None = None
    priority: str = "none"


@router.post("/cards")
def create_card(body: CreateCardRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    with get_db() as conn:
        col = conn.execute(
            "SELECT id FROM columns_ WHERE id = ? AND board_id = ?", (body.column_id, board_id)
        ).fetchone()
        if not col:
            return Response(content='{"error":"Column not found"}', status_code=404, media_type="application/json")

        position = conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 as pos FROM cards WHERE column_id = ?", (body.column_id,)
        ).fetchone()["pos"]

        priority = body.priority if body.priority in VALID_PRIORITIES else "none"
        conn.execute(
            "INSERT INTO cards (column_id, title, details, position, due_date, priority) VALUES (?, ?, ?, ?, ?, ?)",
            (body.column_id, body.title, body.details or "", position, body.due_date, priority),
        )
        conn.commit()
        card_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
        _log_activity(conn, board_id, user_id, "card_created", f'Created card "{body.title}"', card_id)
        conn.commit()

    return {"id": str(card_id), "title": body.title, "details": body.details or "", "due_date": body.due_date, "priority": priority}


class UpdateCardRequest(BaseModel):
    title: str | None = None
    details: str | None = None
    due_date: str | None = None
    priority: str | None = None


@router.put("/cards/{card_id}")
def update_card(card_id: int, body: UpdateCardRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    with get_db() as conn:
        card = conn.execute(
            """SELECT c.id, c.title, c.details, c.due_date, c.priority FROM cards c
               JOIN columns_ col ON c.column_id = col.id
               WHERE c.id = ? AND col.board_id = ?""",
            (card_id, board_id),
        ).fetchone()
        if not card:
            return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

        title = body.title if body.title is not None else card["title"]
        details = body.details if body.details is not None else card["details"]
        due_date = body.due_date if body.due_date is not None else card["due_date"]
        priority = body.priority if body.priority is not None and body.priority in VALID_PRIORITIES else card["priority"]
        conn.execute(
            "UPDATE cards SET title = ?, details = ?, due_date = ?, priority = ? WHERE id = ?",
            (title, details, due_date, priority, card_id),
        )
        _log_activity(conn, board_id, user_id, "card_updated", f'Updated card "{title}"', card_id)
        conn.commit()

    return {"id": str(card_id), "title": title, "details": details, "due_date": due_date, "priority": priority}


@router.delete("/cards/{card_id}")
def delete_card(card_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    with get_db() as conn:
        card = conn.execute(
            """SELECT c.id, c.title, c.column_id, c.position FROM cards c
               JOIN columns_ col ON c.column_id = col.id
               WHERE c.id = ? AND col.board_id = ?""",
            (card_id, board_id),
        ).fetchone()
        if not card:
            return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

        conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        conn.execute(
            "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
            (card["column_id"], card["position"]),
        )
        _log_activity(conn, board_id, user_id, "card_deleted", f'Deleted card "{card["title"]}"')
        conn.commit()
    return {"ok": True}


class ReorderRequest(BaseModel):
    card_id: int
    target_column_id: int
    target_position: int


@router.put("/board/reorder")
def reorder(body: ReorderRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    board_id = _get_board_id(user_id)
    with get_db() as conn:
        card = conn.execute(
            """SELECT c.id, c.column_id, c.position FROM cards c
               JOIN columns_ col ON c.column_id = col.id
               WHERE c.id = ? AND col.board_id = ?""",
            (body.card_id, board_id),
        ).fetchone()
        if not card:
            return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

        target_col = conn.execute(
            "SELECT id FROM columns_ WHERE id = ? AND board_id = ?", (body.target_column_id, board_id)
        ).fetchone()
        if not target_col:
            return Response(content='{"error":"Column not found"}', status_code=404, media_type="application/json")

        # Clamp target_position to valid range
        max_pos = conn.execute(
            "SELECT COUNT(*) as cnt FROM cards WHERE column_id = ?", (body.target_column_id,)
        ).fetchone()["cnt"]
        target_position = max(0, min(body.target_position, max_pos))

        old_col_id = card["column_id"]
        old_pos = card["position"]

        if old_col_id == body.target_column_id:
            if old_pos < target_position:
                conn.execute(
                    "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ? AND position <= ?",
                    (old_col_id, old_pos, target_position),
                )
            elif old_pos > target_position:
                conn.execute(
                    "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ? AND position < ?",
                    (old_col_id, target_position, old_pos),
                )
            conn.execute("UPDATE cards SET position = ? WHERE id = ?", (target_position, body.card_id))
        else:
            conn.execute(
                "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
                (old_col_id, old_pos),
            )
            conn.execute(
                "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
                (body.target_column_id, target_position),
            )
            conn.execute(
                "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
                (body.target_column_id, target_position, body.card_id),
            )

        card_title = conn.execute("SELECT title FROM cards WHERE id = ?", (body.card_id,)).fetchone()["title"]
        if old_col_id != body.target_column_id:
            old_col_title = conn.execute("SELECT title FROM columns_ WHERE id = ?", (old_col_id,)).fetchone()["title"]
            new_col_title = conn.execute("SELECT title FROM columns_ WHERE id = ?", (body.target_column_id,)).fetchone()["title"]
            _log_activity(conn, board_id, user_id, "card_moved", f'Moved "{card_title}" from {old_col_title} to {new_col_title}', body.card_id)
        conn.commit()
    return {"ok": True}


# ── Activity feed ──────────────────────────────────────────────────


@router.get("/boards/{board_id}/activity")
def get_board_activity(board_id: int, limit: int = 20, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    if not _can_access_board(user_id, board_id):
        return Response(content='{"error":"Board not found"}', status_code=404, media_type="application/json")

    with get_db() as conn:
        rows = conn.execute(
            """SELECT a.id, a.action, a.detail, a.card_id, a.created_at,
                      u.username, u.display_name
               FROM activity_log a
               JOIN users u ON a.user_id = u.id
               WHERE a.board_id = ?
               ORDER BY a.created_at DESC
               LIMIT ?""",
            (board_id, min(limit, 100)),
        ).fetchall()

    return {
        "activity": [
            {
                "id": r["id"],
                "action": r["action"],
                "detail": r["detail"],
                "card_id": f"card-{r['card_id']}" if r["card_id"] else None,
                "created_at": r["created_at"],
                "user": {"username": r["username"], "display_name": r["display_name"]},
            }
            for r in rows
        ]
    }


# ── Label operations ────────────────────────────────────────────────


class CreateLabelRequest(BaseModel):
    board_id: int
    name: str
    color: str = "#6b7280"


@router.post("/labels")
def create_label(body: CreateLabelRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    if not _verify_board_ownership(user_id, body.board_id):
        return Response(content='{"error":"Board not found"}', status_code=404, media_type="application/json")

    with get_db() as conn:
        conn.execute(
            "INSERT INTO labels (board_id, name, color) VALUES (?, ?, ?)",
            (body.board_id, body.name, body.color),
        )
        conn.commit()
        label_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]

    return {"id": label_id, "name": body.name, "color": body.color}


class UpdateLabelRequest(BaseModel):
    name: str | None = None
    color: str | None = None


@router.put("/labels/{label_id}")
def update_label(label_id: int, body: UpdateLabelRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        label = conn.execute(
            """SELECT l.id, l.name, l.color FROM labels l
               JOIN boards b ON l.board_id = b.id
               WHERE l.id = ? AND b.user_id = ?""",
            (label_id, user_id),
        ).fetchone()
        if not label:
            return Response(content='{"error":"Label not found"}', status_code=404, media_type="application/json")

        name = body.name if body.name is not None else label["name"]
        color = body.color if body.color is not None else label["color"]
        conn.execute("UPDATE labels SET name = ?, color = ? WHERE id = ?", (name, color, label_id))
        conn.commit()

    return {"id": label_id, "name": name, "color": color}


@router.delete("/labels/{label_id}")
def delete_label(label_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        label = conn.execute(
            """SELECT l.id FROM labels l
               JOIN boards b ON l.board_id = b.id
               WHERE l.id = ? AND b.user_id = ?""",
            (label_id, user_id),
        ).fetchone()
        if not label:
            return Response(content='{"error":"Label not found"}', status_code=404, media_type="application/json")

        conn.execute("DELETE FROM labels WHERE id = ?", (label_id,))
        conn.commit()

    return {"ok": True}


class CardLabelRequest(BaseModel):
    card_id: int
    label_id: int


@router.post("/cards/labels")
def add_card_label(body: CardLabelRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        # Verify card belongs to user
        card = conn.execute(
            """SELECT c.id FROM cards c
               JOIN columns_ col ON c.column_id = col.id
               JOIN boards b ON col.board_id = b.id
               WHERE c.id = ? AND b.user_id = ?""",
            (body.card_id, user_id),
        ).fetchone()
        if not card:
            return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

        # Verify label belongs to same board
        label = conn.execute(
            """SELECT l.id FROM labels l
               JOIN boards b ON l.board_id = b.id
               JOIN columns_ col ON col.board_id = b.id
               JOIN cards c ON c.column_id = col.id
               WHERE l.id = ? AND c.id = ?""",
            (body.label_id, body.card_id),
        ).fetchone()
        if not label:
            return Response(content='{"error":"Label not found"}', status_code=404, media_type="application/json")

        existing = conn.execute(
            "SELECT 1 FROM card_labels WHERE card_id = ? AND label_id = ?",
            (body.card_id, body.label_id),
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO card_labels (card_id, label_id) VALUES (?, ?)",
                (body.card_id, body.label_id),
            )
            conn.commit()

    return {"ok": True}


@router.delete("/cards/{card_id}/labels/{label_id}")
def remove_card_label(card_id: int, label_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        card = conn.execute(
            """SELECT c.id FROM cards c
               JOIN columns_ col ON c.column_id = col.id
               JOIN boards b ON col.board_id = b.id
               WHERE c.id = ? AND b.user_id = ?""",
            (card_id, user_id),
        ).fetchone()
        if not card:
            return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

        conn.execute(
            "DELETE FROM card_labels WHERE card_id = ? AND label_id = ?",
            (card_id, label_id),
        )
        conn.commit()

    return {"ok": True}


# ── Board access check (owner OR member) ──────────────────────────


def _can_access_board(user_id: int, board_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            """SELECT 1 FROM boards WHERE id = ? AND user_id = ?
               UNION
               SELECT 1 FROM board_members WHERE board_id = ? AND user_id = ?""",
            (board_id, user_id, board_id, user_id),
        ).fetchone()
        return row is not None


def _verify_card_access(conn, card_id: int, user_id: int):
    """Check that a card exists and the user can access its board. Returns the card row or None."""
    return conn.execute(
        """SELECT c.id, b.id as board_id FROM cards c
           JOIN columns_ col ON c.column_id = col.id
           JOIN boards b ON col.board_id = b.id
           WHERE c.id = ? AND (b.user_id = ? OR EXISTS (
               SELECT 1 FROM board_members bm WHERE bm.board_id = b.id AND bm.user_id = ?
           ))""",
        (card_id, user_id, user_id),
    ).fetchone()


# ── Comments ───────────────────────────────────────────────────────


class CreateCommentRequest(BaseModel):
    content: str


@router.get("/cards/{card_id}/comments")
def list_comments(card_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        if not _verify_card_access(conn, card_id, user_id):
            return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

        rows = conn.execute(
            """SELECT cm.id, cm.content, cm.created_at, u.id as user_id, u.username, u.display_name
               FROM comments cm
               JOIN users u ON cm.user_id = u.id
               WHERE cm.card_id = ?
               ORDER BY cm.created_at""",
            (card_id,),
        ).fetchall()

    return {
        "comments": [
            {
                "id": r["id"],
                "content": r["content"],
                "created_at": r["created_at"],
                "user": {"id": r["user_id"], "username": r["username"], "display_name": r["display_name"]},
            }
            for r in rows
        ]
    }


@router.post("/cards/{card_id}/comments")
def create_comment(card_id: int, body: CreateCommentRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    if not body.content.strip():
        return Response(content='{"error":"Comment cannot be empty"}', status_code=400, media_type="application/json")

    with get_db() as conn:
        if not _verify_card_access(conn, card_id, user_id):
            return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

        conn.execute(
            "INSERT INTO comments (card_id, user_id, content) VALUES (?, ?, ?)",
            (card_id, user_id, body.content.strip()),
        )
        conn.commit()
        comment_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]

        user = conn.execute("SELECT username, display_name FROM users WHERE id = ?", (user_id,)).fetchone()

    return {
        "id": comment_id,
        "content": body.content.strip(),
        "created_at": None,
        "user": {"id": user_id, "username": user["username"], "display_name": user["display_name"]},
    }


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        comment = conn.execute(
            "SELECT id, user_id FROM comments WHERE id = ?", (comment_id,)
        ).fetchone()
        if not comment or comment["user_id"] != user_id:
            return Response(content='{"error":"Comment not found"}', status_code=404, media_type="application/json")

        conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        conn.commit()

    return {"ok": True}


# ── Board members ──────────────────────────────────────────────────


class AddMemberRequest(BaseModel):
    username: str
    role: str = "member"


@router.post("/boards/{board_id}/members")
def add_board_member(board_id: int, body: AddMemberRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    if not _verify_board_ownership(user_id, board_id):
        return Response(content='{"error":"Only board owner can add members"}', status_code=403, media_type="application/json")

    with get_db() as conn:
        target = conn.execute("SELECT id, username, display_name FROM users WHERE username = ?", (body.username,)).fetchone()
        if not target:
            return Response(content='{"error":"User not found"}', status_code=404, media_type="application/json")

        if target["id"] == user_id:
            return Response(content='{"error":"Cannot add yourself as member"}', status_code=400, media_type="application/json")

        existing = conn.execute(
            "SELECT 1 FROM board_members WHERE board_id = ? AND user_id = ?", (board_id, target["id"])
        ).fetchone()
        if existing:
            return Response(content='{"error":"User is already a member"}', status_code=409, media_type="application/json")

        role = body.role if body.role in ("member", "admin") else "member"
        conn.execute(
            "INSERT INTO board_members (board_id, user_id, role) VALUES (?, ?, ?)",
            (board_id, target["id"], role),
        )
        conn.commit()

    return {"id": target["id"], "username": target["username"], "display_name": target["display_name"], "role": role}


@router.delete("/boards/{board_id}/members/{member_id}")
def remove_board_member(board_id: int, member_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    if not _verify_board_ownership(user_id, board_id):
        return Response(content='{"error":"Only board owner can remove members"}', status_code=403, media_type="application/json")

    with get_db() as conn:
        conn.execute(
            "DELETE FROM board_members WHERE board_id = ? AND user_id = ?", (board_id, member_id)
        )
        conn.commit()

    return {"ok": True}


@router.get("/boards/{board_id}/members")
def list_board_members(board_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    if not _can_access_board(user_id, board_id):
        return Response(content='{"error":"Board not found"}', status_code=404, media_type="application/json")

    with get_db() as conn:
        owner = conn.execute(
            """SELECT u.id, u.username, u.display_name FROM users u
               JOIN boards b ON b.user_id = u.id WHERE b.id = ?""",
            (board_id,),
        ).fetchone()

        members = conn.execute(
            """SELECT u.id, u.username, u.display_name, bm.role
               FROM board_members bm
               JOIN users u ON bm.user_id = u.id
               WHERE bm.board_id = ?""",
            (board_id,),
        ).fetchall()

    result = [{"id": owner["id"], "username": owner["username"], "display_name": owner["display_name"], "role": "owner"}] if owner else []
    result += [{"id": m["id"], "username": m["username"], "display_name": m["display_name"], "role": m["role"]} for m in members]

    return {"members": result}


# ── Card assignments ───────────────────────────────────────────────


class AssignCardRequest(BaseModel):
    user_id: int


@router.post("/cards/{card_id}/assign")
def assign_card(card_id: int, body: AssignCardRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        card = _verify_card_access(conn, card_id, user_id)
        if not card:
            return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

        target_can_access = _can_access_board(body.user_id, card["board_id"])
        if not target_can_access:
            return Response(content='{"error":"User is not a board member"}', status_code=400, media_type="application/json")

        existing = conn.execute(
            "SELECT 1 FROM card_assignments WHERE card_id = ? AND user_id = ?", (card_id, body.user_id)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO card_assignments (card_id, user_id) VALUES (?, ?)", (card_id, body.user_id)
            )
            conn.commit()

        user = conn.execute("SELECT id, username, display_name FROM users WHERE id = ?", (body.user_id,)).fetchone()

    return {"id": user["id"], "username": user["username"], "display_name": user["display_name"]}


@router.delete("/cards/{card_id}/assign/{target_user_id}")
def unassign_card(card_id: int, target_user_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        if not _verify_card_access(conn, card_id, user_id):
            return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

        conn.execute(
            "DELETE FROM card_assignments WHERE card_id = ? AND user_id = ?", (card_id, target_user_id)
        )
        conn.commit()

    return {"ok": True}


# ── Checklist items ───────────────────────────────────────────────


class CreateChecklistItemRequest(BaseModel):
    title: str


class UpdateChecklistItemRequest(BaseModel):
    title: str | None = None
    checked: bool | None = None


@router.get("/cards/{card_id}/checklist")
def list_checklist_items(card_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        if not _verify_card_access(conn, card_id, user_id):
            return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

        rows = conn.execute(
            "SELECT id, title, checked, position FROM checklist_items WHERE card_id = ? ORDER BY position",
            (card_id,),
        ).fetchall()

    return {
        "items": [
            {"id": r["id"], "title": r["title"], "checked": bool(r["checked"]), "position": r["position"]}
            for r in rows
        ]
    }


@router.post("/cards/{card_id}/checklist")
def create_checklist_item(card_id: int, body: CreateChecklistItemRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    if not body.title.strip():
        return Response(content='{"error":"Title cannot be empty"}', status_code=400, media_type="application/json")

    with get_db() as conn:
        if not _verify_card_access(conn, card_id, user_id):
            return Response(content='{"error":"Card not found"}', status_code=404, media_type="application/json")

        position = conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 as pos FROM checklist_items WHERE card_id = ?",
            (card_id,),
        ).fetchone()["pos"]

        conn.execute(
            "INSERT INTO checklist_items (card_id, title, position) VALUES (?, ?, ?)",
            (card_id, body.title.strip(), position),
        )
        conn.commit()
        item_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]

    return {"id": item_id, "title": body.title.strip(), "checked": False, "position": position}


@router.put("/checklist/{item_id}")
def update_checklist_item(item_id: int, body: UpdateChecklistItemRequest, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        item = conn.execute(
            """SELECT ci.id, ci.title, ci.checked, b.id as board_id FROM checklist_items ci
               JOIN cards c ON ci.card_id = c.id
               JOIN columns_ col ON c.column_id = col.id
               JOIN boards b ON col.board_id = b.id
               WHERE ci.id = ?""",
            (item_id,),
        ).fetchone()
        if not item or not _can_access_board(user_id, item["board_id"]):
            return Response(content='{"error":"Item not found"}', status_code=404, media_type="application/json")

        title = body.title.strip() if body.title is not None else item["title"]
        checked = int(body.checked) if body.checked is not None else item["checked"]
        conn.execute(
            "UPDATE checklist_items SET title = ?, checked = ? WHERE id = ?",
            (title, checked, item_id),
        )
        conn.commit()

    return {"id": item_id, "title": title, "checked": bool(checked)}


@router.delete("/checklist/{item_id}")
def delete_checklist_item(item_id: int, session: str = Cookie(default="")):
    user_id, err = require_auth(session)
    if err:
        return err

    with get_db() as conn:
        item = conn.execute(
            """SELECT ci.id, ci.card_id, ci.position, b.id as board_id FROM checklist_items ci
               JOIN cards c ON ci.card_id = c.id
               JOIN columns_ col ON c.column_id = col.id
               JOIN boards b ON col.board_id = b.id
               WHERE ci.id = ?""",
            (item_id,),
        ).fetchone()
        if not item or not _can_access_board(user_id, item["board_id"]):
            return Response(content='{"error":"Item not found"}', status_code=404, media_type="application/json")

        conn.execute("DELETE FROM checklist_items WHERE id = ?", (item_id,))
        conn.execute(
            "UPDATE checklist_items SET position = position - 1 WHERE card_id = ? AND position > ?",
            (item["card_id"], item["position"]),
        )
        conn.commit()

    return {"ok": True}
