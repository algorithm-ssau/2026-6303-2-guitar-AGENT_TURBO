"""Тесты POST /api/chat — проверка подключения к реальному пайплайну."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.agent.service import InvalidRouterResponseError, LLMUnavailableError


@pytest.fixture
def client():
    """Фикстура для создания тестового клиента."""
    return TestClient(app)


class TestRouterLive:
    """Интеграционные тесты для POST /api/chat с реальным пайплайном."""

    def test_search_query_returns_search_mode(self, client):
        """POST /api/chat с поисковым запросом → mode='search', results не пустой."""
        with patch("backend.search.router.interpret_query") as mock_iq:
            mock_iq.return_value = {
                "mode": "search",
                "results": [
                    {
                        "id": "1",
                        "title": "Fender Stratocaster",
                        "price": 800.0,
                        "currency": "USD",
                        "image_url": "https://example.com/img.jpg",
                        "listing_url": "https://reverb.com/item/1",
                    }
                ],
                "search_params": {
                    "search_queries": ["Fender Stratocaster"],
                    "price_max": 1000,
                    "type": "stratocaster",
                },
            }

            response = client.post(
                "/api/chat",
                json={"query": "Найди Fender Stratocaster до 1000$"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "search"
        assert isinstance(data["results"], list)
        assert len(data["results"]) > 0
        assert "title" in data["results"][0]
        assert "listingUrl" in data["results"][0]
        assert data["searchParams"]["type"] == "stratocaster"

    def test_consultation_query_returns_consultation_mode(self, client):
        """POST /api/chat с консультационным запросом → mode='consultation', answer не пустой."""
        with patch("backend.search.router.interpret_query") as mock_iq:
            mock_iq.return_value = {
                "mode": "consultation",
                "answer": "Хамбакер — это тип звукоснимателя с двумя катушками.",
            }

            response = client.post(
                "/api/chat",
                json={"query": "Что такое хамбакер?"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "consultation"
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0

    def test_empty_query_returns_422(self, client):
        """POST /api/chat с пустым query → 422 (validation error)."""
        response = client.post(
            "/api/chat",
            json={"query": ""}
        )
        assert response.status_code == 422

    def test_missing_query_returns_422(self, client):
        """POST /api/chat без query → 422 (validation error)."""
        response = client.post(
            "/api/chat",
            json={}
        )
        assert response.status_code == 422

    def test_llm_unavailable_returns_503(self, client):
        """POST /api/chat мапит недоступную LLM в 503."""
        with patch("backend.search.router.interpret_query", side_effect=LLMUnavailableError("no key")):
            response = client.post("/api/chat", json={"query": "Найди Telecaster"})

        assert response.status_code == 503
        assert "detail" in response.json()

    def test_invalid_router_response_returns_502(self, client):
        """POST /api/chat мапит невалидный router response в 502."""
        with patch("backend.search.router.interpret_query", side_effect=InvalidRouterResponseError("bad json")):
            response = client.post("/api/chat", json={"query": "Найди Telecaster"})

        assert response.status_code == 502
        assert "detail" in response.json()
