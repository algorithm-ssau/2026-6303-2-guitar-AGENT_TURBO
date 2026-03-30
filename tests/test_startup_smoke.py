"""Smoke-тесты запуска проекта — проверка что всё работает без внешних зависимостей."""

import pytest
from fastapi.testclient import TestClient


def test_backend_main_imports():
    """backend/main.py импортируется без ошибок."""
    from backend.main import app
    assert app is not None


def test_fastapi_app_created():
    """FastAPI app создаётся с правильным заголовком."""
    from backend.main import app
    assert app.title == "Guitar Agent API"


def test_root_endpoint_returns_ok():
    """GET / → {"status": "ok"}."""
    from backend.main import app
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_websocket_chat_accepts_connection():
    """WebSocket /chat принимает соединение."""
    from backend.main import app
    client = TestClient(app)
    with client.websocket_connect("/chat") as ws:
        # Сервер отправляет начальный статус при подключении
        data = ws.receive_json()
        assert data["type"] == "status"


def test_post_api_chat_not_500():
    """POST /api/chat работает (не 500)."""
    from backend.main import app
    client = TestClient(app)
    response = client.post(
        "/api/chat",
        json={"query": "Тестовый запрос"}
    )
    # Может быть 200 (успех) — но не 500
    assert response.status_code != 500
    assert response.status_code == 200
