"""Тесты health-check эндпоинтов."""

from fastapi.testclient import TestClient


def _reset_history_connection(db_path: str) -> None:
    """Перенастроить history service на изолированную БД."""
    import backend.history.service as history_service

    if history_service._connection is not None:
        history_service._connection.close()
    history_service._DB_PATH = db_path
    history_service._connection = None


def test_health_endpoint_returns_all_checks(tmp_path, monkeypatch):
    db_path = str(tmp_path / "health.db")
    monkeypatch.setenv("CHAT_DB_PATH", db_path)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("USE_MOCK_REVERB", "true")
    monkeypatch.setenv("REVERB_API_TOKEN", "token")
    _reset_history_connection(db_path)

    from backend.main import app

    with TestClient(app) as client:
        response = client.get("/api/health/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {
            "database": True,
            "llm_configured": True,
            "mock_mode": True,
            "reverb_api_configured": True,
        },
        "version": "0.7.0",
    }


def test_health_ping_returns_pong(tmp_path, monkeypatch):
    db_path = str(tmp_path / "health_ping.db")
    monkeypatch.setenv("CHAT_DB_PATH", db_path)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    _reset_history_connection(db_path)

    from backend.main import app

    with TestClient(app) as client:
        response = client.get("/api/health/ping")

    assert response.status_code == 200
    assert response.json() == {"pong": True}


def test_health_without_groq_api_key_is_degraded(tmp_path, monkeypatch):
    db_path = str(tmp_path / "health_degraded.db")
    monkeypatch.setenv("CHAT_DB_PATH", db_path)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("USE_MOCK_REVERB", "false")
    monkeypatch.delenv("REVERB_API_TOKEN", raising=False)
    _reset_history_connection(db_path)

    from backend.main import app

    with TestClient(app) as client:
        response = client.get("/api/health/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["database"] is True
    assert data["checks"]["llm_configured"] is False
    assert data["checks"]["mock_mode"] is False
    assert data["checks"]["reverb_api_configured"] is False
