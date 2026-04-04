"""
Тесты формата ответа Reverb API с JSON-фикстурами.

Используют формат, максимально близкий к реальному Reverb API.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from backend.search.search_reverb import (
    _deduplicate_listings,
    _filter_by_price,
    _normalize_reverb_response,
    _search_reverb_api,
)

# JSON-фикстура с реальным форматом ответа Reverb API
REVERB_API_RESPONSE_FIXTURE = {
    "listings": [
        {
            "id": 123,
            "title": "Fender Stratocaster 2020",
            "price": {"amount": "499.00", "currency": "USD"},
            "_links": {
                "photo": {"href": "https://images.reverb.com/fender-strat.jpg"},
                "web": {"href": "https://reverb.com/item/123"},
            },
        },
        {
            "id": 123,  # Дубликат для проверки дедупликации
            "title": "Fender Stratocaster 2020",
            "price": {"amount": "499.00", "currency": "USD"},
            "_links": {
                "photo": {"href": "https://images.reverb.com/fender-strat.jpg"},
                "web": {"href": "https://reverb.com/item/123"},
            },
        },
        {
            "id": 456,
            "title": "Gibson Les Paul 2019",
            "price": {"amount": "1200.00", "currency": "USD"},
            "_links": {
                "photo": {"href": "https://images.reverb.com/gibson-lp.jpg"},
                "web": {"href": "https://reverb.com/item/456"},
            },
        },
        {
            "id": 789,
            "title": "Ibanez RG550",
            "price": {"amount": "350.00", "currency": "USD"},
            "_links": {
                "photo": {"href": "https://images.reverb.com/ibanez-rg.jpg"},
                "web": {"href": "https://reverb.com/item/789"},
            },
        },
    ],
}


class TestReverbApiFormatNormalization:
    """Тесты нормализации реального формата Reverb API."""

    def test_normalizes_price_from_string_to_float(self):
        """Цена из строки '499.00' преобразуется в число 499.0."""
        listing = REVERB_API_RESPONSE_FIXTURE["listings"][0]
        result = _normalize_reverb_response(listing)

        assert result["price"] == 499.0
        assert isinstance(result["price"], float)

    def test_normalizes_currency(self):
        """Валюта извлекается из price.currency."""
        listing = REVERB_API_RESPONSE_FIXTURE["listings"][0]
        result = _normalize_reverb_response(listing)

        assert result["currency"] == "USD"

    def test_normalizes_image_from_links_photo_href(self):
        """Изображение извлекается из _links.photo.href."""
        listing = REVERB_API_RESPONSE_FIXTURE["listings"][0]
        result = _normalize_reverb_response(listing)

        assert result["image_url"] == "https://images.reverb.com/fender-strat.jpg"

    def test_normalizes_listing_url_from_links_web_href(self):
        """URL листинга извлекается из _links.web.href."""
        listing = REVERB_API_RESPONSE_FIXTURE["listings"][0]
        result = _normalize_reverb_response(listing)

        assert result["listing_url"] == "https://reverb.com/item/123"

    def test_normalizes_id_to_string(self):
        """ID преобразуется в строку."""
        listing = REVERB_API_RESPONSE_FIXTURE["listings"][0]
        result = _normalize_reverb_response(listing)

        assert result["id"] == "123"
        assert isinstance(result["id"], str)

    def test_all_required_fields_present(self):
        """Все обязательные поля присутствуют в результате."""
        listing = REVERB_API_RESPONSE_FIXTURE["listings"][0]
        result = _normalize_reverb_response(listing)

        required_fields = {"id", "title", "price", "currency", "image_url", "listing_url"}
        assert required_fields.issubset(result.keys())


class TestDeduplication:
    """Тесты дедупликации по id."""

    def test_duplicate_ids_removed(self):
        """Дубликаты с одинаковым id удаляются."""
        normalized = [
            _normalize_reverb_response(l)
            for l in REVERB_API_RESPONSE_FIXTURE["listings"]
        ]

        result = _deduplicate_listings(normalized)

        # 4 элемента с одним дубликатом → 3 уникальных
        assert len(result) == 3

    def test_unique_ids_preserved(self):
        """Уникальные id сохраняются."""
        normalized = [
            _normalize_reverb_response(l)
            for l in REVERB_API_RESPONSE_FIXTURE["listings"]
        ]

        result = _deduplicate_listings(normalized)
        ids = [item["id"] for item in result]

        assert "123" in ids
        assert "456" in ids
        assert "789" in ids


class TestPriceFilteringAfterNormalization:
    """Тесты фильтрации по цене после нормализации."""

    def test_filter_by_price_range(self):
        """Фильтрация по диапазону цен после нормализации."""
        normalized = [
            _normalize_reverb_response(l)
            for l in REVERB_API_RESPONSE_FIXTURE["listings"]
        ]
        deduped = _deduplicate_listings(normalized)

        result = _filter_by_price(deduped, price_min=400, price_max=600)

        # Только Fender Stratocaster (499) попадает в диапазон 400-600
        assert len(result) == 1
        assert result[0]["price"] == 499.0

    def test_filter_by_max_price(self):
        """Фильтрация только по максимальной цене."""
        normalized = [
            _normalize_reverb_response(l)
            for l in REVERB_API_RESPONSE_FIXTURE["listings"]
        ]
        deduped = _deduplicate_listings(normalized)

        result = _filter_by_price(deduped, price_min=None, price_max=500)

        # Fender (499) и Ibanez (350)
        assert len(result) == 2
        assert all(item["price"] <= 500 for item in result)

    def test_filter_by_min_price(self):
        """Фильтрация только по минимальной цене."""
        normalized = [
            _normalize_reverb_response(l)
            for l in REVERB_API_RESPONSE_FIXTURE["listings"]
        ]
        deduped = _deduplicate_listings(normalized)

        result = _filter_by_price(deduped, price_min=1000, price_max=None)

        # Только Gibson Les Paul (1200)
        assert len(result) == 1
        assert result[0]["price"] == 1200.0


class TestReverbApiRequestWithFixture:
    """Тесты запроса к API с мокнутыми ответами."""

    def test_request_uses_correct_url(self):
        """Запрос использует правильный URL /api/listings/all."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = REVERB_API_RESPONSE_FIXTURE

        with patch("backend.search.search_reverb.requests.get") as mock_get, \
             patch.dict(os.environ, {"REVERB_API_TOKEN": "test-token"}):
            mock_get.return_value = mock_response

            _search_reverb_api(["Fender"])

            call_args = mock_get.call_args
            assert call_args.args[0] == "https://api.reverb.com/api/listings/all"

    def test_request_contains_auth_header(self):
        """Запрос содержит заголовок Authorization с Bearer-токеном."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = REVERB_API_RESPONSE_FIXTURE

        with patch("backend.search.search_reverb.requests.get") as mock_get, \
             patch.dict(os.environ, {"REVERB_API_TOKEN": "my-secret-token"}):
            mock_get.return_value = mock_response

            _search_reverb_api(["Gibson"])

            headers = mock_get.call_args.kwargs["headers"]
            assert headers["Authorization"] == "Bearer my-secret-token"

    def test_response_is_deduplicated(self):
        """Результат запроса проходит дедупликацию."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Фикстура содержит 2 элемента с id=123
        mock_response.json.return_value = REVERB_API_RESPONSE_FIXTURE

        with patch("backend.search.search_reverb.requests.get") as mock_get, \
             patch.dict(os.environ, {"REVERB_API_TOKEN": "test-token"}):
            mock_get.return_value = mock_response

            result = _search_reverb_api(["Fender"])

            # После дедупликации: 3 уникальных (123, 456, 789)
            assert len(result) == 3

    def test_response_is_normalized(self):
        """Результат запроса проходит нормализацию — price это число."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = REVERB_API_RESPONSE_FIXTURE

        with patch("backend.search.search_reverb.requests.get") as mock_get, \
             patch.dict(os.environ, {"REVERB_API_TOKEN": "test-token"}):
            mock_get.return_value = mock_response

            result = _search_reverb_api(["Fender"])

            # Все цены — числа (float)
            for item in result:
                assert isinstance(item["price"], (int, float))
                assert isinstance(item["id"], str)
