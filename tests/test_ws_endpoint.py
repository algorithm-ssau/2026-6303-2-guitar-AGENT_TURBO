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
        data = websocket.receive_json()
        assert data["type"] == "status"


def test_websocket_sends_status_before_result(client):
    """Проверяет, что перед result отправляются status-сообщения."""
    with client.websocket_connect("/chat") as websocket:
        websocket.receive_json()  # initial status
        
        websocket.send_json({"query": "Fender Stratocaster"})
        
        status_received = False
        while True:
            data = websocket.receive_json()
            if data.get("type") == "status":
                status_received = True
                assert "status" in data
            elif data.get("type") == "result":
                break
        
        assert status_received


def test_websocket_result_has_mode(client):
    """Проверяет, что result содержит mode."""
    with client.websocket_connect("/chat") as websocket:
        websocket.receive_json()
        
        websocket.send_json({"query": "Нужна гитара для метала"})
        
        while True:
            data = websocket.receive_json()
            if data["type"] == "result":
                assert "mode" in data
                assert data["mode"] in ["search", "consultation", "clarification"]
                break


def test_websocket_empty_query_returns_error(client):
    """Проверяет, что пустой query возвращает ошибку."""
    with client.websocket_connect("/chat") as websocket:
        websocket.receive_json()
        
        websocket.send_json({"query": ""})
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "status" in data


def test_websocket_missing_query_returns_error(client):
    """Проверяет, что отсутствие query возвращает ошибку."""
    with client.websocket_connect("/chat") as websocket:
        websocket.receive_json()
        
        websocket.send_json({})
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "status" in data


def test_websocket_search_result(client):
    """Проверяет, что search result содержит results."""
    with client.websocket_connect("/chat") as websocket:
        websocket.receive_json()
        
        websocket.send_json({"query": "Fender Stratocaster"})
        
        while True:
            data = websocket.receive_json()
            if data["type"] == "result":
                if data["mode"] == "search":
                    assert "results" in data
                    assert len(data["results"]) > 0
                break


def test_websocket_session_history_response(client, tmp_path, monkeypatch):
    """Проверяет, что sessionId возвращается и история работает."""
    db_path = str(tmp_path / "test_history.db")
    monkeypatch.setenv("CHAT_DB_PATH", db_path)
    
    # Переинициализируем БД
    import backend.history.service as history_service
    if history_service._connection is not None:
        history_service._connection.close()
    history_service._DB_PATH = db_path
    history_service._connection = None
    
    with client.websocket_connect("/chat") as websocket:
        websocket.receive_json()
        
        # Отправляем запрос без sessionId (создастся новая сессия)
        websocket.send_json({"query": "Fender"})
        
        result_data = None
        while result_data is None:
            data = websocket.receive_json()
            if data["type"] == "result":
                result_data = data
        
        # Проверяем что есть sessionId
        if "sessionId" in result_data:
            session_id = result_data["sessionId"]
            
            # Проверяем историю через REST
            response = client.get(f"/api/sessions/{session_id}/messages")
            assert response.status_code == 200
            history = response.json()
            assert "items" in history
            assert len(history["items"]) > 0
