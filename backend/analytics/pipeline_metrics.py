"""Метрики пайплайна обработки сообщений."""

from math import ceil
from typing import Optional

from backend.history.service import _get_connection
from backend.utils.logger import get_logger

logger = get_logger("analytics")


def init_metrics_table() -> None:
    """Создать таблицу метрик пайплайна, если она ещё не существует."""
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            mode TEXT NOT NULL,
            elapsed_ms INTEGER NOT NULL,
            results_count INTEGER,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );
    """)
    conn.commit()
    logger.info("Таблица pipeline_metrics инициализирована")


def record_exchange(
    session_id: Optional[int],
    mode: str,
    elapsed_ms: int,
    results_count: Optional[int],
) -> None:
    """Записать метрику одного обмена сообщениями."""
    conn = _get_connection()
    conn.execute(
        "INSERT INTO pipeline_metrics (session_id, mode, elapsed_ms, results_count) VALUES (?, ?, ?, ?)",
        (session_id, mode, elapsed_ms, results_count),
    )
    conn.commit()
    logger.info("Записана метрика pipeline_metrics: session_id=%s mode=%s", session_id, mode)


def compute_kpi(user_id: int) -> dict:
    """Посчитать KPI по сохранённым метрикам пайплайна."""
    conn = _get_connection()

    total_sessions = _scalar_int(
        conn.execute(
            "SELECT COUNT(DISTINCT pipeline_metrics.session_id) "
            "FROM pipeline_metrics "
            "JOIN sessions ON sessions.id = pipeline_metrics.session_id "
            "WHERE sessions.user_id = ?",
            (user_id,),
        )
    )
    total_exchanges = _scalar_int(
        conn.execute(
            "SELECT COUNT(*) "
            "FROM pipeline_metrics "
            "JOIN sessions ON sessions.id = pipeline_metrics.session_id "
            "WHERE sessions.user_id = ?",
            (user_id,),
        )
    )
    avg_elapsed_ms = _scalar_float(
        conn.execute(
            "SELECT AVG(elapsed_ms) "
            "FROM pipeline_metrics "
            "JOIN sessions ON sessions.id = pipeline_metrics.session_id "
            "WHERE sessions.user_id = ?",
            (user_id,),
        )
    )
    elapsed_values = [
        int(row[0])
        for row in conn.execute(
            "SELECT elapsed_ms "
            "FROM pipeline_metrics "
            "JOIN sessions ON sessions.id = pipeline_metrics.session_id "
            "WHERE sessions.user_id = ? "
            "ORDER BY elapsed_ms ASC",
            (user_id,),
        ).fetchall()
    ]

    p95_elapsed_ms = _percentile_95(elapsed_values)
    avg_messages_to_first_search = _avg_messages_to_first_search(user_id)
    clarification_rate = _session_rate("clarification", total_sessions, user_id)
    repeat_session_rate = _repeat_search_rate(total_sessions, user_id)

    return {
        "total_sessions": total_sessions,
        "total_exchanges": total_exchanges,
        "avg_elapsed_ms": avg_elapsed_ms,
        "p95_elapsed_ms": p95_elapsed_ms,
        "avg_messages_to_first_search": avg_messages_to_first_search,
        "clarification_rate": clarification_rate,
        "repeat_session_rate": repeat_session_rate,
        "kpi_met": avg_messages_to_first_search <= 3,
    }


def _scalar_int(cursor) -> int:
    row = cursor.fetchone()
    return int(row[0] or 0) if row else 0


def _scalar_float(cursor) -> float:
    row = cursor.fetchone()
    return float(row[0] or 0) if row else 0.0


def _percentile_95(values: list[int]) -> float:
    if not values:
        return 0.0
    index = max(0, ceil(len(values) * 0.95) - 1)
    return float(values[index])


def _avg_messages_to_first_search(user_id: int) -> float:
    conn = _get_connection()
    first_search_rows = conn.execute(
        "SELECT pipeline_metrics.session_id, MIN(pipeline_metrics.id) AS first_search_id "
        "FROM pipeline_metrics "
        "JOIN sessions ON sessions.id = pipeline_metrics.session_id "
        "WHERE pipeline_metrics.mode = 'search' AND sessions.user_id = ? "
        "GROUP BY pipeline_metrics.session_id",
        (user_id,),
    ).fetchall()

    if not first_search_rows:
        return 0.0

    positions = []
    for row in first_search_rows:
        before_count = _scalar_int(
            conn.execute(
                "SELECT COUNT(*) FROM pipeline_metrics WHERE session_id = ? AND id < ?",
                (row["session_id"], row["first_search_id"]),
            )
        )
        positions.append(max(before_count, 1))

    return round(sum(positions) / len(positions), 2)


def _session_rate(mode: str, total_sessions: int, user_id: int) -> float:
    if total_sessions == 0:
        return 0.0

    conn = _get_connection()
    matching_sessions = _scalar_int(
        conn.execute(
            "SELECT COUNT(DISTINCT pipeline_metrics.session_id) "
            "FROM pipeline_metrics "
            "JOIN sessions ON sessions.id = pipeline_metrics.session_id "
            "WHERE pipeline_metrics.mode = ? AND sessions.user_id = ?",
            (mode, user_id),
        )
    )
    return round(matching_sessions / total_sessions * 100, 2)


def _repeat_search_rate(total_sessions: int, user_id: int) -> float:
    if total_sessions == 0:
        return 0.0

    conn = _get_connection()
    repeat_sessions = _scalar_int(
        conn.execute(
            "SELECT COUNT(*) FROM ("
            "SELECT pipeline_metrics.session_id FROM pipeline_metrics "
            "JOIN sessions ON sessions.id = pipeline_metrics.session_id "
            "WHERE pipeline_metrics.mode = 'search' AND sessions.user_id = ? "
            "GROUP BY pipeline_metrics.session_id HAVING COUNT(*) >= 2"
            ")",
            (user_id,),
        )
    )
    return round(repeat_sessions / total_sessions * 100, 2)
