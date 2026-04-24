"""Тесты endpoint-а метрик пайплайна."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def metrics_client(tmp_path, monkeypatch):
    """TestClient с изолированной SQLite-БД."""
    db_path = str(tmp_path / "metrics_endpoint.db")
    monkeypatch.setenv("CHAT_DB_PATH", db_path)

    import backend.history.service as history_service

    if history_service._connection is not None:
        history_service._connection.close()
    history_service._DB_PATH = db_path
    history_service._connection = None

    from backend.main import app

    with TestClient(app) as client:
        yield client

    if history_service._connection is not None:
        history_service._connection.close()
    history_service._connection = None


def test_metrics_health_returns_all_fields(metrics_client):
    response = metrics_client.get("/api/metrics/health")

    assert response.status_code == 200
    assert response.json() == {
        "totalSessions": 0,
        "totalExchanges": 0,
        "avgElapsedMs": 0.0,
        "p95ElapsedMs": 0.0,
        "avgMessagesToFirstSearch": 0.0,
        "clarificationRate": 0.0,
        "repeatSessionRate": 0.0,
        "kpiMet": True,
    }


def test_metrics_health_updates_after_record_exchange(metrics_client):
    from backend.analytics.pipeline_metrics import record_exchange

    record_exchange(1, "search", 250, 3)

    response = metrics_client.get("/api/metrics/health")

    assert response.status_code == 200
    data = response.json()
    assert data["totalSessions"] == 1
    assert data["totalExchanges"] == 1
    assert data["avgElapsedMs"] == 250.0
    assert data["kpiMet"] is True
