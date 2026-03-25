"""
Тесты для модуля поиска Reverb.
"""

import json
import os
from unittest.mock import patch

import pytest
import requests
import responses

from backend.search.search_reverb import search_reverb


class TestSearchReverbMockMode:
    """Тесты для мок-режима работы search_reverb."""

    def test_mock_mode_returns_list(self):
        """Проверяет, что функция возвращает список в мок-режиме."""
        os.environ["USE_MOCK_REVERB"] = "true"
        
        result = search_reverb(search_queries=["Fender Stratocaster"])
        
        assert isinstance(result, list)
        assert len(result) > 0

    def test_mock_mode_format(self):
        """Проверяет формат возвращаемых данных в мок-режиме."""
        os.environ["USE_MOCK_REVERB"] = "true"
        
        result = search_reverb(search_queries=["Gibson Les Paul"])
        
        # Проверяем структуру каждого элемента
        for item in result:
            assert "id" in item
            assert "title" in item
            assert "price" in item
            assert "currency" in item
            assert "image_url" in item
            assert "listing_url" in item

    def test_mock_mode_price_filter_min(self):
        """Проверяет фильтрацию по минимальной цене."""
        os.environ["USE_MOCK_REVERB"] = "true"
        
        result = search_reverb(
            search_queries=["Guitar"],
            price_min=500,
        )
        
        # Все результаты должны быть >= 500
        for item in result:
            assert item["price"] >= 500

    def test_mock_mode_price_filter_max(self):
        """Проверяет фильтрацию по максимальной цене."""
        os.environ["USE_MOCK_REVERB"] = "true"
        
        result = search_reverb(
            search_queries=["Guitar"],
            price_max=500,
        )
        
        # Все результаты должны быть <= 500
        for item in result:
            assert item["price"] <= 500

    def test_mock_mode_price_filter_range(self):
        """Проверяет фильтрацию по диапазону цен."""
        os.environ["USE_MOCK_REVERB"] = "true"
        
        result = search_reverb(
            search_queries=["Guitar"],
            price_min=400,
            price_max=800,
        )
        
        # Все результаты должны быть в диапазоне 400-800
        for item in result:
            assert 400 <= item["price"] <= 800

    def test_mock_mode_empty_queries(self):
        """Проверяет работу с пустым списком запросов."""
        os.environ["USE_MOCK_REVERB"] = "true"
        
        result = search_reverb(search_queries=[])
        
        # В мок-режиме должен вернуть все данные (без фильтрации по query)
        assert isinstance(result, list)

    def test_mock_mode_no_price_filter(self):
        """Проверяет работу без фильтрации по цене."""
        os.environ["USE_MOCK_REVERB"] = "true"
        
        result = search_reverb(search_queries=["Ibanez"])
        
        # Должен вернуть все данные без фильтрации по цене
        assert isinstance(result, list)
        assert len(result) == 5  # Все 5 моков из mock_reverb.json


class TestSearchReverbRealMode:
    """Тесты для реального режима работы с мок-HTTP."""

    @responses.activate
    def test_real_mode_api_request_format(self):
        """Проверяет, что параметры правильно преобразуются в URL запроса."""
        # Убираем мок-режим
        os.environ["USE_MOCK_REVERB"] = "false"
        
        # Мок-ответ от Reverb API
        mock_response = {
            "listings": [
                {
                    "id": 12345,
                    "title": "Fender Stratocaster",
                    "price": {"amount": 1000, "currency": "USD"},
                    "image_url": "https://example.com/image.jpg",
                    "url": "https://reverb.com/item/12345",
                }
            ]
        }
        
        # Регистрируем мок-ответ
        responses.add(
            responses.GET,
            "https://api.reverb.com/api/listings",
            json=mock_response,
            status=200,
        )
        
        result = search_reverb(
            search_queries=["Fender Stratocaster"],
            price_min=800,
            price_max=1200,
        )
        
        # Проверяем, что был сделан запрос
        assert len(responses.calls) == 1
        
        # Проверяем параметры запроса
        request = responses.calls[0].request
        assert "query=Fender+Stratocaster" in request.url or "query=Fender%20Stratocaster" in request.url
        assert "price_min=800" in request.url
        assert "price_max=1200" in request.url
        
        # Проверяем результат
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Fender Stratocaster"
        assert result[0]["price"] == 1000

    @responses.activate
    def test_real_mode_response_parsing(self):
        """Проверяет корректность парсинга ответа от Reverb API."""
        os.environ["USE_MOCK_REVERB"] = "false"
        
        # Мок-ответ с альтернативной структурой цен
        mock_response = {
            "listings": [
                {
                    "id": "item_001",
                    "name": "Gibson Les Paul",
                    "price": 1500,
                    "photos": [{"url": "https://example.com/gibson.jpg"}],
                    "web_url": "https://reverb.com/item/001",
                },
                {
                    "id": "item_002",
                    "name": "PRS Custom 24",
                    "price": {"amount": 2000, "currency": "USD"},
                    "image_url": "https://example.com/prs.jpg",
                    "url": "https://reverb.com/item/002",
                }
            ]
        }
        
        responses.add(
            responses.GET,
            "https://api.reverb.com/api/listings",
            json=mock_response,
            status=200,
        )
        
        result = search_reverb(search_queries=["Guitar"])
        
        assert len(result) == 2
        
        # Проверяем нормализацию разных форматов
        assert result[0]["id"] == "item_001"
        assert result[0]["title"] == "Gibson Les Paul"
        assert result[0]["price"] == 1500
        
        assert result[1]["id"] == "item_002"
        assert result[1]["title"] == "PRS Custom 24"
        assert result[1]["price"] == 2000

    @responses.activate
    def test_real_mode_fallback_to_mock_on_empty_response(self):
        """Проверяет fallback на мок-данные при пустом ответе API."""
        os.environ["USE_MOCK_REVERB"] = "false"
        
        # Пустой ответ от API
        mock_response = {"listings": []}
        
        responses.add(
            responses.GET,
            "https://api.reverb.com/api/listings",
            json=mock_response,
            status=200,
        )
        
        result = search_reverb(search_queries=["Rare Guitar"])
        
        # Должен вернуться к мок-данным как fallback
        assert isinstance(result, list)
        assert len(result) > 0


class TestSearchReverbEdgeCases:
    """Тесты на граничные случаи работы search_reverb."""

    @responses.activate
    def test_http_500_error(self):
        """Проверяет обработку HTTP 500 ошибки от API."""
        os.environ["USE_MOCK_REVERB"] = "false"
        
        # Сервер возвращает 500 ошибку
        responses.add(
            responses.GET,
            "https://api.reverb.com/api/listings",
            status=500,
        )
        
        result = search_reverb(search_queries=["Guitar"])
        
        # Должен вернуться к мок-данным при ошибке API
        assert isinstance(result, list)
        assert len(result) > 0

    @responses.activate
    def test_http_timeout(self):
        """Проверяет обработку таймаута запроса."""
        os.environ["USE_MOCK_REVERB"] = "false"
        
        # Симулируем таймаут
        responses.add(
            responses.GET,
            "https://api.reverb.com/api/listings",
            body=requests.exceptions.Timeout("Request timed out"),
        )
        
        result = search_reverb(search_queries=["Guitar"])
        
        # Должен вернуться к мок-данным при таймауте
        assert isinstance(result, list)
        assert len(result) > 0

    @responses.activate
    def test_http_connection_error(self):
        """Проверяет обработку ошибки соединения."""
        os.environ["USE_MOCK_REVERB"] = "false"
        
        # Симулируем ошибку соединения
        responses.add(
            responses.GET,
            "https://api.reverb.com/api/listings",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )
        
        result = search_reverb(search_queries=["Guitar"])
        
        # Должен вернуться к мок-данным при ошибке соединения
        assert isinstance(result, list)
        assert len(result) > 0

    @responses.activate
    def test_multiple_search_queries(self):
        """Проверяет обработку нескольких поисковых запросов."""
        os.environ["USE_MOCK_REVERB"] = "false"
        
        # Мок-ответы для разных запросов
        mock_response_1 = {
            "listings": [
                {
                    "id": 1,
                    "title": "Fender Strat",
                    "price": {"amount": 1000, "currency": "USD"},
                    "image_url": "https://example.com/fender.jpg",
                    "url": "https://reverb.com/item/1",
                }
            ]
        }
        mock_response_2 = {
            "listings": [
                {
                    "id": 2,
                    "title": "Gibson Les Paul",
                    "price": {"amount": 1500, "currency": "USD"},
                    "image_url": "https://example.com/gibson.jpg",
                    "url": "https://reverb.com/item/2",
                }
            ]
        }
        
        responses.add(
            responses.GET,
            "https://api.reverb.com/api/listings",
            json=mock_response_1,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://api.reverb.com/api/listings",
            json=mock_response_2,
            status=200,
        )
        
        result = search_reverb(
            search_queries=["Fender", "Gibson"],
            price_min=800,
            price_max=2000,
        )
        
        # Должны объединиться результаты обоих запросов
        assert len(result) == 2
        titles = [item["title"] for item in result]
        assert "Fender Strat" in titles
        assert "Gibson Les Paul" in titles

    @responses.activate
    def test_price_filtering_on_api_results(self):
        """Проверяет фильтрацию результатов API по цене."""
        os.environ["USE_MOCK_REVERB"] = "false"
        
        mock_response = {
            "listings": [
                {
                    "id": 1,
                    "title": "Cheap Guitar",
                    "price": {"amount": 200, "currency": "USD"},
                    "image_url": "https://example.com/cheap.jpg",
                    "url": "https://reverb.com/item/1",
                },
                {
                    "id": 2,
                    "title": "Expensive Guitar",
                    "price": {"amount": 2000, "currency": "USD"},
                    "image_url": "https://example.com/expensive.jpg",
                    "url": "https://reverb.com/item/2",
                },
                {
                    "id": 3,
                    "title": "Mid-Range Guitar",
                    "price": {"amount": 800, "currency": "USD"},
                    "image_url": "https://example.com/mid.jpg",
                    "url": "https://reverb.com/item/3",
                }
            ]
        }
        
        responses.add(
            responses.GET,
            "https://api.reverb.com/api/listings",
            json=mock_response,
            status=200,
        )
        
        result = search_reverb(
            search_queries=["Guitar"],
            price_min=500,
            price_max=1500,
        )
        
        # Должна остаться только Mid-Range Guitar (800)
        assert len(result) == 1
        assert result[0]["title"] == "Mid-Range Guitar"
        assert result[0]["price"] == 800

    def test_mock_mode_price_edge_zero(self):
        """Проверяет фильтрацию при price_min=0."""
        os.environ["USE_MOCK_REVERB"] = "true"
        
        result = search_reverb(
            search_queries=["Guitar"],
            price_min=0,
            price_max=100,
        )
        
        # Должны остаться только товары <= 100
        for item in result:
            assert item["price"] <= 100

    def test_mock_mode_price_no_upper_limit(self):
        """Проверяет фильтрацию только по минимальной цене."""
        os.environ["USE_MOCK_REVERB"] = "true"
        
        result = search_reverb(
            search_queries=["Guitar"],
            price_min=900,
        )
        
        # Должны остаться только товары >= 900
        for item in result:
            assert item["price"] >= 900
