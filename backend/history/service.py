"""Логика хранения истории чата в SQLite с поддержкой сессий."""

import json
import os
import re
import sqlite3
from typing import Optional

from fastapi import HTTPException, status
from backend.history.row_mappers import (
    message_row_to_dict,
    session_row_to_dict,
    session_state_row_to_dict,
)
from backend.utils.logger import get_logger

logger = get_logger("history")

_DB_PATH = os.environ.get(
    "CHAT_DB_PATH",
    os.path.join(os.path.dirname(__file__), "chat.db"),
)

_connection: Optional[sqlite3.Connection] = None

_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", flags=re.IGNORECASE | re.DOTALL)
_DANGLING_THINK_BLOCK_RE = re.compile(r"<think>.*$", flags=re.IGNORECASE | re.DOTALL)


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
            user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
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
            search_params TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );

        CREATE TABLE IF NOT EXISTS session_state (
            session_id INTEGER PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
            state      TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );
    """)
    try:
        conn.execute("ALTER TABLE chat_history ADD COLUMN search_params TEXT")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            raise
    try:
        conn.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            raise
    _strip_think_blocks_from_existing_answers(conn)
    conn.commit()
    from backend.analytics.pipeline_metrics import init_metrics_table; init_metrics_table()
    logger.info("БД истории инициализирована: %s", _DB_PATH)


def strip_think_blocks(text: Optional[str]) -> Optional[str]:
    """Удаляет model reasoning blocks из сохраняемого/читаемого текста."""
    if text is None:
        return None
    cleaned = _THINK_BLOCK_RE.sub("", str(text))
    cleaned = _DANGLING_THINK_BLOCK_RE.sub("", cleaned)
    return cleaned.strip()


def _strip_think_blocks_from_existing_answers(conn: sqlite3.Connection) -> int:
    """One-time cleanup для старых ответов, где reasoning сохранился в answer."""
    rows = conn.execute(
        "SELECT id, answer FROM chat_history WHERE answer LIKE '%<think%'"
    ).fetchall()
    updated = 0
    for row in rows:
        answer = row["answer"] if isinstance(row, sqlite3.Row) else row[1]
        cleaned = strip_think_blocks(answer)
        if cleaned != answer:
            row_id = row["id"] if isinstance(row, sqlite3.Row) else row[0]
            conn.execute("UPDATE chat_history SET answer = ? WHERE id = ?", (cleaned, row_id))
            updated += 1
    if updated:
        logger.info("Очищены <think> блоки в истории: %d записей", updated)
    return updated


def create_session(title: str, user_id: int) -> int:
    """Создать новую сессию. Возвращает id."""
    conn = _get_connection()
    cursor = conn.execute(
        "INSERT INTO sessions (user_id, title) VALUES (?, ?)",
        (user_id, title[:100]),
    )
    conn.commit()
    logger.info("Создана сессия #%d: %s", cursor.lastrowid, title[:50])
    return cursor.lastrowid


def get_sessions(user_id: int, offset: int = 0, limit: int = 20) -> tuple[list[dict], int]:
    """Получить список сессий с пагинацией (от новых к старым).
    
    Возвращает кортеж: (список сессий, общее количество).
    """
    conn = _get_connection()
    # Считаем общее количество
    total_row = conn.execute("SELECT COUNT(*) FROM sessions WHERE user_id = ?", (user_id,)).fetchone()
    total = total_row[0]

    # Выбираем с пагинацией
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at FROM sessions "
        "WHERE user_id = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (user_id, limit, offset),
    ).fetchall()
    return [session_row_to_dict(row) for row in rows], total


def get_session_messages(session_id: int, user_id: Optional[int] = None) -> list[dict]:
    """Получить все сообщения сессии (от старых к новым)."""
    conn = _get_connection()
    if user_id is not None:
        ensure_session_owner(session_id, user_id)

    rows = conn.execute(
        "SELECT id, session_id, user_query, mode, answer, results, search_params, created_at "
        "FROM chat_history WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    ).fetchall()

    return [message_row_to_dict(row) for row in rows]


def save_exchange(
    session_id: int,
    user_query: str,
    mode: str,
    answer: Optional[str] = None,
    results: Optional[list] = None,
    search_params: Optional[dict] = None,
) -> int:
    """Сохранить пару запрос-ответ. Возвращает id записи."""
    conn = _get_connection()
    answer = strip_think_blocks(answer)
    cursor = conn.execute(
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
    # Обновляем updated_at у сессии
    conn.execute(
        "UPDATE sessions SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?",
        (session_id,),
    )
    conn.commit()
    logger.info("Сохранена запись #%d в сессии #%d", cursor.lastrowid, session_id)
    return cursor.lastrowid


def ensure_session_owner(session_id: int, user_id: int) -> None:
    """Проверить, что сессия принадлежит пользователю."""
    conn = _get_connection()
    row = conn.execute(
        "SELECT id FROM sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id),
    ).fetchone()
    if row:
        return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Сессия не найдена.",
    )


def delete_session(session_id: int, user_id: int) -> None:
    """Удалить сессию и все её сообщения."""
    conn = _get_connection()
    ensure_session_owner(session_id, user_id)
    conn.execute("DELETE FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
    conn.commit()
    logger.info("Удалена сессия #%d", session_id)


def get_session_state(session_id: int) -> dict:
    """Возвращает структурированное состояние поискового контекста сессии."""
    conn = _get_connection()
    row = conn.execute(
        "SELECT state FROM session_state WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    return session_state_row_to_dict(row)


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


def clear_history(user_id: int) -> int:
    """Очистить всю историю. Возвращает количество удалённых сессий."""
    conn = _get_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM sessions WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    logger.info("Очищена история: %d сессий", count)
    return count
