from app.db import get_db


def apply_actions(actions: list[dict], board_id: int) -> list[dict]:
    """Apply a list of AI actions to the board. Returns results for each action."""
    results = []
    for action in actions:
        action_type = action.get("type")
        if action_type == "create_card":
            results.append(_create_card(action, board_id))
        elif action_type == "update_card":
            results.append(_update_card(action, board_id))
        elif action_type == "delete_card":
            results.append(_delete_card(action, board_id))
        elif action_type == "move_card":
            results.append(_move_card(action, board_id))
        else:
            results.append({"ok": False, "error": f"Unknown action type: {action_type}"})
    return results


def _create_card(action: dict, board_id: int) -> dict:
    column_id = action.get("column_id")
    title = action.get("title", "")
    details = action.get("details", "") or ""

    with get_db() as conn:
        col = conn.execute(
            "SELECT id FROM columns_ WHERE id = ? AND board_id = ?", (column_id, board_id)
        ).fetchone()
        if not col:
            return {"ok": False, "error": f"Column {column_id} not found"}

        position = conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 as pos FROM cards WHERE column_id = ?", (column_id,)
        ).fetchone()["pos"]

        conn.execute(
            "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
            (column_id, title, details, position),
        )
        conn.commit()
        card_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
    return {"ok": True, "type": "create_card", "card_id": card_id}


def _update_card(action: dict, board_id: int) -> dict:
    card_id = action.get("card_id")

    with get_db() as conn:
        card = conn.execute(
            """SELECT c.id, c.title, c.details FROM cards c
               JOIN columns_ col ON c.column_id = col.id
               WHERE c.id = ? AND col.board_id = ?""",
            (card_id, board_id),
        ).fetchone()
        if not card:
            return {"ok": False, "error": f"Card {card_id} not found"}

        title = action.get("title") if action.get("title") is not None else card["title"]
        details = action.get("details") if action.get("details") is not None else card["details"]
        conn.execute("UPDATE cards SET title = ?, details = ? WHERE id = ?", (title, details, card_id))
        conn.commit()
    return {"ok": True, "type": "update_card", "card_id": card_id}


def _delete_card(action: dict, board_id: int) -> dict:
    card_id = action.get("card_id")

    with get_db() as conn:
        card = conn.execute(
            """SELECT c.id, c.column_id, c.position FROM cards c
               JOIN columns_ col ON c.column_id = col.id
               WHERE c.id = ? AND col.board_id = ?""",
            (card_id, board_id),
        ).fetchone()
        if not card:
            return {"ok": False, "error": f"Card {card_id} not found"}

        conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        conn.execute(
            "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
            (card["column_id"], card["position"]),
        )
        conn.commit()
    return {"ok": True, "type": "delete_card", "card_id": card_id}


def _move_card(action: dict, board_id: int) -> dict:
    card_id = action.get("card_id")
    target_column_id = action.get("column_id")
    target_position = action.get("position", 0) or 0

    with get_db() as conn:
        card = conn.execute(
            """SELECT c.id, c.column_id, c.position FROM cards c
               JOIN columns_ col ON c.column_id = col.id
               WHERE c.id = ? AND col.board_id = ?""",
            (card_id, board_id),
        ).fetchone()
        if not card:
            return {"ok": False, "error": f"Card {card_id} not found"}

        target_col = conn.execute(
            "SELECT id FROM columns_ WHERE id = ? AND board_id = ?", (target_column_id, board_id)
        ).fetchone()
        if not target_col:
            return {"ok": False, "error": f"Column {target_column_id} not found"}

        old_col_id = card["column_id"]
        old_pos = card["position"]

        if old_col_id == target_column_id:
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
            conn.execute("UPDATE cards SET position = ? WHERE id = ?", (target_position, card_id))
        else:
            conn.execute(
                "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
                (old_col_id, old_pos),
            )
            conn.execute(
                "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
                (target_column_id, target_position),
            )
            conn.execute(
                "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
                (target_column_id, target_position, card_id),
            )

        conn.commit()
    return {"ok": True, "type": "move_card", "card_id": card_id}
