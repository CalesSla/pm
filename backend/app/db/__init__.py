import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import bcrypt

DB_PATH = Path(os.environ.get("DB_PATH", "data/pm.db"))

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS boards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL DEFAULT 'My Board',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS columns_ (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id INTEGER NOT NULL REFERENCES boards(id),
    title TEXT NOT NULL,
    position INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    column_id INTEGER NOT NULL REFERENCES columns_(id),
    title TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    position INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

DEFAULT_COLUMNS = ["Backlog", "Discovery", "In Progress", "Review", "Done"]

SEED_CARDS = [
    (0, "Align roadmap themes", "Draft quarterly themes with impact statements and metrics."),
    (0, "Gather customer signals", "Review support tags, sales notes, and churn feedback."),
    (1, "Prototype analytics view", "Sketch initial dashboard layout and key drill-downs."),
    (2, "Refine status language", "Standardize column labels and tone across the board."),
    (2, "Design card layout", "Add hierarchy and spacing for scanning dense lists."),
    (3, "QA micro-interactions", "Verify hover, focus, and loading states."),
    (4, "Ship marketing page", "Final copy approved and asset pack delivered."),
    (4, "Close onboarding sprint", "Document release notes and share internally."),
]


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA_SQL)

        existing = conn.execute("SELECT id FROM users WHERE username = ?", ("user",)).fetchone()
        if not existing:
            pw_hash = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode()
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("user", pw_hash))
            conn.commit()

            user_id = conn.execute("SELECT id FROM users WHERE username = ?", ("user",)).fetchone()["id"]
            conn.execute("INSERT INTO boards (user_id, title) VALUES (?, ?)", (user_id, "My Board"))
            conn.commit()

            board_id = conn.execute("SELECT id FROM boards WHERE user_id = ?", (user_id,)).fetchone()["id"]
            column_ids = []
            for pos, title in enumerate(DEFAULT_COLUMNS):
                conn.execute(
                    "INSERT INTO columns_ (board_id, title, position) VALUES (?, ?, ?)",
                    (board_id, title, pos),
                )
                conn.commit()
                col_id = conn.execute(
                    "SELECT id FROM columns_ WHERE board_id = ? AND position = ?",
                    (board_id, pos),
                ).fetchone()["id"]
                column_ids.append(col_id)

            for col_idx, title, details in SEED_CARDS:
                card_pos = conn.execute(
                    "SELECT COUNT(*) as cnt FROM cards WHERE column_id = ?",
                    (column_ids[col_idx],),
                ).fetchone()["cnt"]
                conn.execute(
                    "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
                    (column_ids[col_idx], title, details, card_pos),
                )
            conn.commit()
