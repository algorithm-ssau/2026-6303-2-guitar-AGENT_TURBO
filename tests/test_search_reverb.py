"""
Тесты для search_reverb с моковыми данными.
"""

import os
import pytest

from backend.search.search_reverb import search_reverb


class TestSearchReverbMockData:
    """Тесты для поиска по моковым данным Reverb."""

    @pytest.fixture(autouse=True)
    def setup_mock_mode(self):
        """Автоматически включаем мок-режим для всех тестов."""
        os.environ["USE_MOCK_REVERB"] = "true"

    def test_search_by_brand_finds_results(self):
        """Поиск по бренду находит соответствующие гитары."""
        result = search_reverb(["Fender"])
        
        assert len(result) > 0
        # Все результаты содержат "Fender" в названии
        for item in result:
            assert "fender" in item["title"].lower()

    def test_search_nonexistent_returns_empty(self):
        """Поиск несуществующего бренда возвращает пустой список."""
        result = search_reverb(["несуществующий"])
        
        assert result == []

    def test_filter_by_price_max(self):
        """Фильтрация по максимальной цене."""
        result = search_reverb([], price_max=500)
        
        assert len(result) > 0
        for item in result:
            assert item["price"] <= 500

    def test_filter_by_price_range(self):
        """Фильтрация по диапазону цен."""
        result = search_reverb([], price_min=800, price_max=2000)
        
        for item in result:
            assert 800 <= item["price"] <= 2000

    def test_combined_search_and_price_filter(self):
        """Комбинация поиска по названию и фильтрации по цене."""
        result = search_reverb(["Gibson"], price_min=800, price_max=2000)
        
        for item in result:
            assert "gibson" in item["title"].lower()
            assert 800 <= item["price"] <= 2000

    def test_empty_query_returns_all_in_budget(self):
        """Пустой запрос возвращает все гитары в рамках бюджета."""
        result = search_reverb([], price_min=300, price_max=700)
        
        assert len(result) > 0
        for item in result:
            assert 300 <= item["price"] <= 700

    def test_result_format_required_fields(self):
        """Формат результата содержит обязательные поля."""
        result = search_reverb(["Guitar"])
        
        assert len(result) > 0
        required_fields = {"id", "title", "price", "currency", "listing_url"}
        
        for item in result:
            assert required_fields.issubset(item.keys())
            # Проверяем типы данных
            assert isinstance(item["id"], str)
            assert isinstance(item["title"], str)
            assert isinstance(item["price"], (int, float))
            assert isinstance(item["currency"], str)
            assert isinstance(item["listing_url"], str)

    def test_search_by_brand_ibanez(self):
        """Поиск по бренду Ibanez находит соответствующие гитары."""
        result = search_reverb(["Ibanez"])
        
        assert len(result) > 0
        for item in result:
            assert "ibanez" in item["title"].lower()

    def test_search_acoustic_guitars(self):
        """Поиск акустических гитар находит соответствующие объявления."""
        result = search_reverb(["Acoustic"])
        
        assert len(result) > 0
        for item in result:
            assert "acoustic" in item["title"].lower()

    def test_search_7string_metal_guitars(self):
        """Поиск 7-струнных гитар для метала."""
        result = search_reverb(["7-String"])
        
        assert len(result) > 0
        for item in result:
            assert "7-string" in item["title"].lower()

    def test_price_min_only(self):
        """Фильтрация только по минимальной цене."""
        result = search_reverb([], price_min=2000)
        
        assert len(result) > 0
        for item in result:
            assert item["price"] >= 2000

    def test_case_insensitive_search(self):
        """Регистронезависимый поиск."""
        result_lower = search_reverb(["fender"])
        result_upper = search_reverb(["FENDER"])
        result_mixed = search_reverb(["FeNdEr"])
        
        # Все должны вернуть одинаковый результат
        assert len(result_lower) == len(result_upper) == len(result_mixed)
        assert len(result_lower) > 0
