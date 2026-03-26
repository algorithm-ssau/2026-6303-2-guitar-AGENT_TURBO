"""Тесты WebSocket endpoint для чата."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Создаёт тестовый клиент."""
    return TestClient(app)


def test_websocket_connect(client):
    """Проверяет, что WebSocket подключается к /chat."""
    with client.websocket_connect("/chat") as websocket:
        # Получаем начальное сообщение со статусом
        data = websocket.receive_json()
        assert data["type"] == "status"


def test_websocket_sends_result_with_mode(client):
    """Проверяет, что отправка query возвращает result с mode."""
    with client.websocket_connect("/chat") as websocket:
        # Получаем начальное сообщение
        websocket.receive_json()
        
        # Отправляем запрос
        websocket.send_json({"query": "Нужна гитара для метала"})
        
        # Получаем сообщения пока не найдём result
        received_result = False
        while not received_result:
            data = websocket.receive_json()
            if data["type"] == "result":
                received_result = True
                assert "mode" in data
                assert data["mode"] in ["search", "consultation"]


def test_websocket_empty_query_returns_error(client):
    """Проверяет, что пустой query возвращает ошибку."""
    with client.websocket_connect("/chat") as websocket:
        # Получаем начальное сообщение
        websocket.receive_json()
        
        # Отправляем пустой запрос
        websocket.send_json({"query": ""})
        
        # Получаем ошибку
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "status" in data
