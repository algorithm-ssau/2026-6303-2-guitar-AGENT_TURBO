"""Тесты метрик пайплайна."""

import sqlite3

import pytest


@pytest.fixture
def metrics_db(tmp_path, monkeypatch):
    """Изолированная SQLite-БД для метрик."""
    db_path = str(tmp_path / "pipeline_metrics.db")
    monkeypatch.setenv("CHAT_DB_PATH", db_path)

    import backend.history.service as history_service

    if history_service._connection is not None:
        history_service._connection.close()
    history_service._DB_PATH = db_path
    history_service._connection = None

    yield db_path

    if history_service._connection is not None:
        history_service._connection.close()
    history_service._connection = None


def test_init_metrics_table_creates_table(metrics_db):
    from backend.analytics.pipeline_metrics import init_metrics_table

    init_metrics_table()

    conn = sqlite3.connect(metrics_db)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'pipeline_metrics'"
    ).fetchone()
    conn.close()

    assert row is not None


def test_record_exchange_inserts_row(metrics_db):
    from backend.analytics.pipeline_metrics import init_metrics_table, record_exchange

    init_metrics_table()
    record_exchange(1, "search", 1500, 5)

    conn = sqlite3.connect(metrics_db)
    row = conn.execute(
        "SELECT session_id, mode, elapsed_ms, results_count FROM pipeline_metrics"
    ).fetchone()
    conn.close()

    assert row == (1, "search", 1500, 5)


def test_compute_kpi_empty_db(metrics_db):
    from backend.analytics.pipeline_metrics import compute_kpi, init_metrics_table

    init_metrics_table()

    kpi = compute_kpi()

    assert kpi == {
        "total_sessions": 0,
        "total_exchanges": 0,
        "avg_elapsed_ms": 0.0,
        "p95_elapsed_ms": 0.0,
        "avg_messages_to_first_search": 0.0,
        "clarification_rate": 0.0,
        "repeat_session_rate": 0.0,
        "kpi_met": True,
    }


def test_compute_kpi_averages(metrics_db):
    from backend.analytics.pipeline_metrics import compute_kpi, init_metrics_table, record_exchange

    init_metrics_table()
    for elapsed in [100, 200, 300, 400, 500]:
        record_exchange(1, "search", elapsed, 3)

    kpi = compute_kpi()

    assert kpi["total_sessions"] == 1
    assert kpi["total_exchanges"] == 5
    assert kpi["avg_elapsed_ms"] == 300.0


def test_avg_messages_to_first_search(metrics_db):
    from backend.analytics.pipeline_metrics import compute_kpi, init_metrics_table, record_exchange

    init_metrics_table()
    record_exchange(1, "clarification", 100, None)
    record_exchange(1, "clarification", 100, None)
    record_exchange(1, "clarification", 100, None)
    record_exchange(1, "search", 100, 5)
    record_exchange(2, "search", 100, 5)

    kpi = compute_kpi()

    assert kpi["avg_messages_to_first_search"] == 2.0
    assert kpi["kpi_met"] is True


def test_p95_elapsed_ms(metrics_db):
    from backend.analytics.pipeline_metrics import compute_kpi, init_metrics_table, record_exchange

    init_metrics_table()
    for index in range(1, 101):
        record_exchange(index, "search", index * 100, 1)

    kpi = compute_kpi()

    assert kpi["p95_elapsed_ms"] == 9500.0


def test_clarification_rate(metrics_db):
    from backend.analytics.pipeline_metrics import compute_kpi, init_metrics_table, record_exchange

    init_metrics_table()
    for session_id in range(1, 11):
        mode = "clarification" if session_id <= 3 else "search"
        record_exchange(session_id, mode, 100, None if mode == "clarification" else 1)

    kpi = compute_kpi()

    assert kpi["clarification_rate"] == 30.0


def test_repeat_session_rate(metrics_db):
    from backend.analytics.pipeline_metrics import compute_kpi, init_metrics_table, record_exchange

    init_metrics_table()
    for session_id in range(1, 11):
        record_exchange(session_id, "search", 100, 1)
        if session_id <= 4:
            record_exchange(session_id, "search", 110, 1)

    kpi = compute_kpi()

    assert kpi["repeat_session_rate"] == 40.0
