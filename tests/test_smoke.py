import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Фикстура для создания тестового клиента."""
    return TestClient(app)


class TestSmoke:
    """Smoke-тесты для проверки базовой работоспособности API."""

    def test_app_starts(self, client):
        """Приложение запускается и root endpoint доступен."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_chat_endpoint_available(self, client):
        """Эндпоинт /api/chat доступен."""
        response = client.post(
            "/api/chat",
            json={"query": "test"}
        )
        assert response.status_code == 200

    def test_chat_returns_expected_structure(self, client):
        """/api/chat возвращает ожидаемую структуру."""
        response = client.post(
            "/api/chat",
            json={"query": "Нужна гитара"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "mode" in data
        assert isinstance(data["mode"], str)
