"""
Тесты для реального Reverb API с авторизацией.
"""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestReverbApiAuth:
    """Тесты авторизации и запросов к реальному Reverb API."""

    @pytest.fixture
    def mock_response(self):
        """Создаёт мок ответа Reverb API."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "listings": [
                {
                    "id": 1001,
                    "title": "Fender Stratocaster 2020",
                    "price": {"amount": "499.00", "currency": "USD"},
                    "_links": {
                        "photo": {"href": "https://images.reverb.com/photo.jpg"},
                        "web": {"href": "https://reverb.com/item/1001"},
                    },
                },
            ],
        }
        return response

    def test_request_contains_auth_header(self, mock_response):
        """Запрос к API содержит заголовок Authorization с Bearer-токеном."""
        import requests
        from backend.search.search_reverb import _search_reverb_api

        with patch("backend.search.search_reverb.requests.get") as mock_get, \
             patch.dict(os.environ, {"REVERB_API_TOKEN": "test-token-123"}):
            mock_get.return_value = mock_response

            _search_reverb_api(["Fender"])

            # Проверяем, что requests.get был вызван с правильными headers
            call_kwargs = mock_get.call_args.kwargs
            assert "Authorization" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Authorization"] == "Bearer test-token-123"
            assert call_kwargs["headers"]["Accept-Version"] == "3.0"

    def test_request_uses_correct_endpoint(self, mock_response):
        """Запрос использует правильный URL endpoint."""
        from backend.search.search_reverb import _search_reverb_api

        with patch("backend.search.search_reverb.requests.get") as mock_get, \
             patch.dict(os.environ, {"REVERB_API_TOKEN": "test-token"}):
            mock_get.return_value = mock_response

            _search_reverb_api(["Gibson"])

            # Проверяем URL
            call_args = mock_get.call_args
            assert call_args.args[0] == "https://api.reverb.com/api/listings/all"

    def test_normalization_handles_real_api_format(self, mock_response):
        """Нормализация корректно обрабатывает реальный формат Reverb API."""
        from backend.search.search_reverb import _normalize_reverb_response

        raw_listing = mock_response.json()["listings"][0]
        result = _normalize_reverb_response(raw_listing)

        assert result["id"] == "1001"
        assert result["title"] == "Fender Stratocaster 2020"
        assert result["price"] == 499.0
        assert result["currency"] == "USD"
        assert result["image_url"] == "https://images.reverb.com/photo.jpg"
        assert result["listing_url"] == "https://reverb.com/item/1001"

    def test_fallback_without_token(self):
        """Без REVERB_API_TOKEN возвращается fallback на mock-данные."""
        from backend.search.search_reverb import search_reverb

        # Убеждаемся, что токен не задан и USE_MOCK_REVERB выключен
        env_copy = os.environ.copy()
        env_copy.pop("REVERB_API_TOKEN", None)
        env_copy["USE_MOCK_REVERB"] = "false"

        with patch.dict(os.environ, env_copy, clear=True):
            # Убираем токен и мок-режим, но fallback всё равно сработает
            # потому что search_reverb загружает mock при отсутствии токена
            result = search_reverb(["Fender"], price_min=100, price_max=2000)

            # Должны вернуться данные из mock_reverb.json
            assert len(result) > 0
            assert all("fender" in item["title"].lower() for item in result)
            assert all(100 <= item["price"] <= 2000 for item in result)

    def test_pagination_limits_to_three_queries(self, mock_response):
        """Пагинация ограничивает до 3 запросов."""
        from backend.search.search_reverb import _search_reverb_api

        with patch("backend.search.search_reverb.requests.get") as mock_get, \
             patch.dict(os.environ, {"REVERB_API_TOKEN": "test-token"}):
            mock_get.return_value = mock_response

            _search_reverb_api(["Fender", "Gibson", "PRS", "Ibanez", "Martin"])

            # Должно быть не более 3 запросов
            assert mock_get.call_count <= 3

    def test_deduplication_by_id(self):
        """Одинаковые id — один результат (дедупликация)."""
        from backend.search.search_reverb import (
            _deduplicate_listings,
            _normalize_reverb_response,
        )

        raw_listings = [
            {
                "id": 1001,
                "title": "Fender Stratocaster",
                "price": {"amount": "499.00", "currency": "USD"},
                "_links": {
                    "photo": {"href": "https://images.reverb.com/1.jpg"},
                    "web": {"href": "https://reverb.com/item/1001"},
                },
            },
            {
                "id": 1001,  # Тот же id — дубликат
                "title": "Fender Stratocaster",
                "price": {"amount": "499.00", "currency": "USD"},
                "_links": {
                    "photo": {"href": "https://images.reverb.com/1.jpg"},
                    "web": {"href": "https://reverb.com/item/1001"},
                },
            },
            {
                "id": 1002,
                "title": "Gibson Les Paul",
                "price": {"amount": "999.00", "currency": "USD"},
                "_links": {
                    "photo": {"href": "https://images.reverb.com/2.jpg"},
                    "web": {"href": "https://reverb.com/item/1002"},
                },
            },
        ]

        # Нормализуем
        normalized = [_normalize_reverb_response(l) for l in raw_listings]

        # Дедуплицируем
        result = _deduplicate_listings(normalized)

        assert len(result) == 2  # Только 2 уникальных id
        ids = [item["id"] for item in result]
        assert "1001" in ids
        assert "1002" in ids
