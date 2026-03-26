"""End-to-end тесты через WebSocket для полного пайплайна."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app


class MockLLMClient:
    """Мок LLM-клиента для e2e тестов."""

    def ask(self, text: str, system_prompt: str) -> str:
        return "Хамбакеры дают более плотный и насыщенный звук по сравнению с синглами."

    def extract_search_params(self, text: str) -> dict:
        return {
            "search_queries": ["Fender Stratocaster"],
            "price_min": None,
            "price_max": 1000,
        }


@pytest.fixture
def mock_llm():
    """Патчим create_llm_client чтобы не зависеть от Groq API."""
    with patch("backend.agent.service.create_llm_client", return_value=MockLLMClient()):
        yield


def test_search_flow(mock_llm):
    """Полный search flow → серия status сообщений → финальный result с mode=search."""
    client = TestClient(app)
    with client.websocket_connect("/chat") as ws:
        ws.send_json({"query": "Найди Fender Stratocaster до 1000$"})

        messages = []
        # Собираем все сообщения до получения result
        while True:
            msg = ws.receive_json()
            messages.append(msg)
            if msg.get("type") == "result":
                break

        # Проверяем что есть status-сообщения
        status_messages = [m for m in messages if m["type"] == "status"]
        assert len(status_messages) >= 1

        # Проверяем финальный result
        result = messages[-1]
        assert result["type"] == "result"
        assert result["mode"] == "search"
        assert "results" in result


def test_consultation_flow(mock_llm):
    """Полный consultation flow → status → result с mode=consultation, answer не пустой."""
    client = TestClient(app)
    with client.websocket_connect("/chat") as ws:
        ws.send_json({"query": "В чем разница между single-coil и humbucker?"})

        messages = []
        while True:
            msg = ws.receive_json()
            messages.append(msg)
            if msg.get("type") == "result":
                break

        # Проверяем status-сообщения
        status_messages = [m for m in messages if m["type"] == "status"]
        assert len(status_messages) >= 1

        # Проверяем финальный result
        result = messages[-1]
        assert result["type"] == "result"
        assert result["mode"] == "consultation"
        assert result["answer"]
        assert len(result["answer"]) > 0


def test_empty_query(mock_llm):
    """Пустой query → type="error"."""
    client = TestClient(app)
    with client.websocket_connect("/chat") as ws:
        ws.send_json({"query": ""})
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert "text" in msg


def test_status_order(mock_llm):
    """Статусы приходят в правильном порядке для search-запроса."""
    client = TestClient(app)
    with client.websocket_connect("/chat") as ws:
        ws.send_json({"query": "Найди Gibson Les Paul до 2000$"})

        messages = []
        while True:
            msg = ws.receive_json()
            messages.append(msg)
            if msg.get("type") == "result":
                break

        status_texts = [m["text"] for m in messages if m["type"] == "status"]

        # Проверяем правильный порядок статусов для search
        expected_order = [
            "Определяю режим...",
            "Генерирую параметры поиска...",
            "Ищу на Reverb...",
            "Ранжирую результаты...",
        ]
        assert status_texts == expected_order
