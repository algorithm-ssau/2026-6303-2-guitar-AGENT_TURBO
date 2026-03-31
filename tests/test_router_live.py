"""Тесты POST /api/chat — проверка подключения к реальному пайплайну."""

import os
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Фикстура для создания тестового клиента."""
    return TestClient(app)


class MockLLMClient:
    """Мок LLM-клиента для тестов роутера."""

    def ask(self, text: str, system_prompt: str) -> str:
        return "Хамбакер — это тип звукоснимателя с двумя катушками."

    def extract_search_params(self, text: str) -> dict:
        return {
            "search_queries": ["Fender Stratocaster"],
            "price_min": None,
            "price_max": 1000,
        }


def mock_search_fn(search_queries, price_min=None, price_max=None):
    """Мок функции поиска."""
    return [
        {
            "id": "1",
            "title": "Fender Stratocaster MIM",
            "price": 800,
            "currency": "USD",
            "image_url": "https://example.com/img.jpg",
            "listing_url": "https://reverb.com/item/1",
        },
    ]


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
        assert "listing_url" in data["results"][0]

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
