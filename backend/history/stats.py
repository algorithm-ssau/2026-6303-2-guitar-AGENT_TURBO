"""Статистика использования системы."""

import sqlite3
from typing import Optional

from backend.utils.logger import get_logger

logger = get_logger("stats")

# Используем ту же БД что и history
_DB_PATH: Optional[str] = None


def _get_db_path() -> str:
    """Получить путь к БД (из env или по умолчанию)."""
    global _DB_PATH
    if _DB_PATH is None:
        import os
        _DB_PATH = os.environ.get(
            "CHAT_DB_PATH",
            os.path.join(os.path.dirname(__file__), "chat.db"),
        )
    return _DB_PATH


def _get_connection() -> sqlite3.Connection:
    """Получить новое соединение для чтения статистики."""
    conn = sqlite3.connect(_get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_stats() -> dict:
    """
    Собрать статистику использования.

    Возвращает:
        - total_sessions: общее количество сессий
        - total_queries: общее количество запросов
        - mode_distribution: распределение по режимам (search, consultation, off_topic)
        - avg_messages_per_session: среднее количество сообщений на сессию
        - avg_queries_with_links: среднее количество запросов с выдачей ссылок (mode=search)
    """
    conn = _get_connection()

    try:
        # Общее количество сессий
        row = conn.execute("SELECT COUNT(*) as cnt FROM sessions").fetchone()
        total_sessions = row["cnt"] if row else 0

        # Общее количество запросов
        row = conn.execute("SELECT COUNT(*) as cnt FROM chat_history").fetchone()
        total_queries = row["cnt"] if row else 0

        # Распределение по режимам
        rows = conn.execute(
            "SELECT mode, COUNT(*) as cnt FROM chat_history GROUP BY mode"
        ).fetchall()
        mode_distribution = {row["mode"]: row["cnt"] for row in rows}

        # Среднее количество сообщений на сессию
        if total_sessions > 0:
            avg_messages = round(total_queries / total_sessions, 2)
        else:
            avg_messages = 0

        # Среднее количество сообщений до выдачи ссылок (search-запросы)
        # Для каждой сессии считаем номер search-запроса, берём средний номер первого search
        search_sessions = conn.execute(
            "SELECT session_id, MIN(id) as first_search_id "
            "FROM chat_history WHERE mode = 'search' "
            "GROUP BY session_id"
        ).fetchall()

        if search_sessions:
            # Для каждой сессии с search: сколько записей было до первого search
            positions = []
            for sess in search_sessions:
                sid = sess["session_id"]
                first_search_id = sess["first_search_id"]
                # Считаем сколько записей было до первого search в этой сессии
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM chat_history "
                    "WHERE session_id = ? AND id < ?",
                    (sid, first_search_id),
                ).fetchone()
                positions.append((row["cnt"] if row else 0) + 1)  # +1 т.к. сам search тоже считается

            avg_queries_with_links = round(sum(positions) / len(positions), 2)
        else:
            avg_queries_with_links = 0

        return {
            "total_sessions": total_sessions,
            "total_queries": total_queries,
            "mode_distribution": mode_distribution,
            "avg_messages_per_session": avg_messages,
            "avg_queries_with_links": avg_queries_with_links,
        }
    finally:
        conn.close()
