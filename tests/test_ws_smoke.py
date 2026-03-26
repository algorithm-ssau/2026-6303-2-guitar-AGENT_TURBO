"""Smoke-тесты WebSocket пайплайна чата."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Создаёт тестовый клиент."""
    return TestClient(app)


def test_consultation_request_returns_status_and_result(client):
    """Сценарий 1: Consultation запрос → получаем type='status', затем type='result' с mode='consultation'."""
    with client.websocket_connect("/chat") as websocket:
        # Получаем начальное сообщение со статусом
        initial_data = websocket.receive_json()
        assert initial_data["type"] == "status"
        assert "Определяю режим" in initial_data.get("status", "")
        
        # Отправляем запрос на консультацию (теоретический вопрос)
        websocket.send_json({"query": "В чем разница между single-coil и humbucker?"})
        
        # Получаем сообщения пока не найдём result
        received_status = False
        received_result = False
        
        while not received_result:
            data = websocket.receive_json()
            
            if data["type"] == "status":
                received_status = True
            elif data["type"] == "result":
                received_result = True
                assert data["mode"] == "consultation"
                assert "answer" in data
        
        # Проверяем что статус был получен
        assert received_status, "Должен быть получен статус перед результатом"


def test_search_request_returns_status_series_and_result(client):
    """Сценарий 2: Search запрос → получаем серию status, затем type='result' с mode='search'."""
    with client.websocket_connect("/chat") as websocket:
        # Получаем начальное сообщение со статусом
        initial_data = websocket.receive_json()
        assert initial_data["type"] == "status"
        
        # Отправляем запрос на поиск (конкретные критерии гитары)
        websocket.send_json({"query": "Нужна 7-струнная гитара для djent, желательно Ibanez"})
        
        # Получаем сообщения и собираем все статусы
        statuses = []
        received_result = False
        result_data = None
        
        while not received_result:
            data = websocket.receive_json()
            
            if data["type"] == "status":
                statuses.append(data.get("status", ""))
            elif data["type"] == "result":
                received_result = True
                result_data = data
        
        # Проверяем что результат получен
        assert received_result, "Должен быть получен результат"
        assert result_data["mode"] == "search"
        assert "results" in result_data
        
        # Проверяем что были статусы (как минимум "Ищу на Reverb..." и "Ранжирую результаты...")
        assert len(statuses) >= 1, "Должны быть получены промежуточные статусы"


def test_empty_query_returns_error(client):
    """Сценарий 3: Пустой query → type='error'."""
    with client.websocket_connect("/chat") as websocket:
        # Получаем начальное сообщение со статусом
        initial_data = websocket.receive_json()
        assert initial_data["type"] == "status"
        
        # Отправляем пустой запрос
        websocket.send_json({"query": ""})
        
        # Получаем ошибку
        data = websocket.receive_json()
        
        assert data["type"] == "error"
        assert "status" in data
        assert "пустым" in data["status"].lower() or "empty" in data["status"].lower()


def test_whitespace_only_query_returns_error(client):
    """Дополнительно: Запрос только с пробелами → type='error'."""
    with client.websocket_connect("/chat") as websocket:
        # Получаем начальное сообщение
        websocket.receive_json()
        
        # Отправляем запрос только с пробелами
        websocket.send_json({"query": "   "})
        
        # Получаем ошибку
        data = websocket.receive_json()
        
        assert data["type"] == "error"
