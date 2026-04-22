"""Логика хранения истории чата в SQLite с поддержкой сессий."""

import json
import os
import sqlite3
from typing import Optional

from backend.utils.logger import get_logger

logger = get_logger("history")

_DB_PATH = os.environ.get(
    "CHAT_DB_PATH",
    os.path.join(os.path.dirname(__file__), "chat.db"),
)

_connection: Optional[sqlite3.Connection] = None


def _get_connection() -> sqlite3.Connection:
    """Получить соединение с БД (lazy singleton)."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(_DB_PATH, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


def init_db() -> None:
    """Создать таблицы, если не существуют."""
    conn = _get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            user_query TEXT NOT NULL,
            mode       TEXT NOT NULL,
            answer     TEXT,
            results    TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );

        CREATE TABLE IF NOT EXISTS session_state (
            session_id INTEGER PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
            state      TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );
    """)
    conn.commit()
    logger.info("БД истории инициализирована: %s", _DB_PATH)


def create_session(title: str) -> int:
    """Создать новую сессию. Возвращает id."""
    conn = _get_connection()
    cursor = conn.execute(
        "INSERT INTO sessions (title) VALUES (?)",
        (title[:100],),
    )
    conn.commit()
    logger.info("Создана сессия #%d: %s", cursor.lastrowid, title[:50])
    return cursor.lastrowid


def get_sessions(offset: int = 0, limit: int = 20) -> tuple[list[dict], int]:
    """Получить список сессий с пагинацией (от новых к старым).
    
    Возвращает кортеж: (список сессий, общее количество).
    """
    conn = _get_connection()
    # Считаем общее количество
    total_row = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()
    total = total_row[0]

    # Выбираем с пагинацией
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at FROM sessions "
        "ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [dict(row) for row in rows], total


def get_session_messages(session_id: int) -> list[dict]:
    """Получить все сообщения сессии (от старых к новым)."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT id, session_id, user_query, mode, answer, results, created_at "
        "FROM chat_history WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    ).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        if item["results"]:
            item["results"] = json.loads(item["results"])
        items.append(item)
    return items


def save_exchange(
    session_id: int,
    user_query: str,
    mode: str,
    answer: Optional[str] = None,
    results: Optional[list] = None,
) -> int:
    """Сохранить пару запрос-ответ. Возвращает id записи."""
    conn = _get_connection()
    cursor = conn.execute(
        "INSERT INTO chat_history (session_id, user_query, mode, answer, results) VALUES (?, ?, ?, ?, ?)",
        (session_id, user_query, mode, answer, json.dumps(results, ensure_ascii=False) if results else None),
    )
    # Обновляем updated_at у сессии
    conn.execute(
        "UPDATE sessions SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?",
        (session_id,),
    )
    conn.commit()
    logger.info("Сохранена запись #%d в сессии #%d", cursor.lastrowid, session_id)
    return cursor.lastrowid


def delete_session(session_id: int) -> None:
    """Удалить сессию и все её сообщения."""
    conn = _get_connection()
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    logger.info("Удалена сессия #%d", session_id)


def get_session_state(session_id: int) -> dict:
    """Возвращает структурированное состояние поискового контекста сессии."""
    conn = _get_connection()
    row = conn.execute(
        "SELECT state FROM session_state WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if not row:
        return {}

    try:
        data = json.loads(row[0])
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def save_session_state(session_id: int, state: dict) -> None:
    """Сохраняет/обновляет структурированное состояние поискового контекста."""
    conn = _get_connection()
    payload = json.dumps(state or {}, ensure_ascii=False)
    conn.execute(
        "INSERT INTO session_state (session_id, state, updated_at) VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now')) "
        "ON CONFLICT(session_id) DO UPDATE SET state = excluded.state, updated_at = excluded.updated_at",
        (session_id, payload),
    )
    conn.commit()


def clear_history() -> int:
    """Очистить всю историю. Возвращает количество удалённых сессий."""
    conn = _get_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM sessions")
    count = cursor.fetchone()[0]
    conn.executescript("DELETE FROM chat_history; DELETE FROM sessions;")
    conn.commit()
    logger.info("Очищена история: %d сессий", count)
    return count
