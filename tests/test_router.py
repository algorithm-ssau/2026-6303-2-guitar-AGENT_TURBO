import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Фикстура для создания тестового клиента."""
    return TestClient(app)


class TestChatRouter:
    """Интеграционные тесты для /api/chat эндпоинта."""

    def test_valid_chat_request_returns_200(self, client):
        """Корректный запрос возвращает 200."""
        response = client.post(
            "/api/chat",
            json={"query": "Нужна гитара для металла до 45 тысяч"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "mode" in data
        assert "answer" in data

    def test_empty_query_returns_422(self, client):
        """Пустой query возвращает 422."""
        response = client.post(
            "/api/chat",
            json={"query": ""}
        )
        assert response.status_code == 422

    def test_missing_query_returns_422(self, client):
        """Отсутствие query возвращает 422."""
        response = client.post(
            "/api/chat",
            json={}
        )
        assert response.status_code == 422

    def test_response_structure(self, client):
        """Проверка структуры ответа."""
        response = client.post(
            "/api/chat",
            json={"query": "Fender Stratocaster"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["mode"], str)
        assert data["mode"] in ["search", "consultation"]
