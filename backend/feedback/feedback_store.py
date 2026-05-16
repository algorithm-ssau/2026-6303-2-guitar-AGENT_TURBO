"""Storage helpers для feedback в SQLite."""

import sqlite3

from .models import FeedbackRequest


def init_feedback_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            guitar_id TEXT NOT NULL,
            rating TEXT NOT NULL CHECK(rating IN ('up','down')),
            query TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );
    """)


def insert_feedback(conn: sqlite3.Connection, req: FeedbackRequest) -> sqlite3.Cursor:
    return conn.execute(
        "INSERT INTO feedback (session_id, guitar_id, rating, query) VALUES (?, ?, ?, ?)",
        (req.session_id, req.guitar_id, req.rating, req.query),
    )


def select_feedback_totals(conn: sqlite3.Connection, user_id: int) -> tuple[int, int, int]:
    row = conn.execute(
        "SELECT COUNT(*), SUM(rating='up'), SUM(rating='down') "
        "FROM feedback WHERE session_id IN (SELECT id FROM sessions WHERE user_id = ?)",
        (user_id,),
    ).fetchone()
    total, up, down = row
    return total or 0, up or 0, down or 0


def select_feedback_by_guitar(conn: sqlite3.Connection, user_id: int) -> dict[str, dict]:
    rows = conn.execute(
        "SELECT guitar_id, SUM(rating='up'), SUM(rating='down') "
        "FROM feedback WHERE session_id IN (SELECT id FROM sessions WHERE user_id = ?) "
        "GROUP BY guitar_id",
        (user_id,),
    ).fetchall()
    return {row[0]: {"up": row[1] or 0, "down": row[2] or 0} for row in rows}
