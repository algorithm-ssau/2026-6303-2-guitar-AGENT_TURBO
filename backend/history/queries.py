"""SQL helpers для операций истории чата."""

import json
import sqlite3
from typing import Optional


def insert_session(conn: sqlite3.Connection, title: str, user_id: int) -> sqlite3.Cursor:
    return conn.execute(
        "INSERT INTO sessions (user_id, title) VALUES (?, ?)",
        (user_id, title[:100]),
    )


def count_sessions(conn: sqlite3.Connection, user_id: int) -> int:
    return conn.execute("SELECT COUNT(*) FROM sessions WHERE user_id = ?", (user_id,)).fetchone()[0]


def select_sessions(conn: sqlite3.Connection, user_id: int, offset: int, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, title, created_at, updated_at FROM sessions "
        "WHERE user_id = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (user_id, limit, offset),
    ).fetchall()


def select_session_messages(conn: sqlite3.Connection, session_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, session_id, user_query, mode, answer, results, search_params, created_at "
        "FROM chat_history WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    ).fetchall()


def insert_exchange(
    conn: sqlite3.Connection,
    session_id: int,
    user_query: str,
    mode: str,
    answer: Optional[str],
    results: Optional[list],
    search_params: Optional[dict],
) -> sqlite3.Cursor:
    return conn.execute(
        "INSERT INTO chat_history (session_id, user_query, mode, answer, results, search_params) VALUES (?, ?, ?, ?, ?, ?)",
        (
            session_id,
            user_query,
            mode,
            answer,
            json.dumps(results, ensure_ascii=False) if results else None,
            json.dumps(search_params, ensure_ascii=False) if search_params else None,
        ),
    )


def touch_session(conn: sqlite3.Connection, session_id: int) -> None:
    conn.execute(
        "UPDATE sessions SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?",
        (session_id,),
    )


def select_owned_session(conn: sqlite3.Connection, session_id: int, user_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT id FROM sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id),
    ).fetchone()


def delete_owned_session(conn: sqlite3.Connection, session_id: int, user_id: int) -> None:
    conn.execute("DELETE FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id))


def select_session_state(conn: sqlite3.Connection, session_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT state FROM session_state WHERE session_id = ?",
        (session_id,),
    ).fetchone()


def upsert_session_state(conn: sqlite3.Connection, session_id: int, state: dict) -> None:
    conn.execute(
        "INSERT INTO session_state (session_id, state, updated_at) VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now')) "
        "ON CONFLICT(session_id) DO UPDATE SET state = excluded.state, updated_at = excluded.updated_at",
        (session_id, json.dumps(state or {}, ensure_ascii=False)),
    )


def delete_user_sessions(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
