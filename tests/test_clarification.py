"""Тесты модуля уточняющих вопросов (clarification)."""

import pytest
from backend.agent.clarification import check_needs_clarification


class TestCheckNeedsClarification:
    """Тесты функции check_needs_clarification."""

    def test_no_budget_no_type_returns_both_question(self):
        """Запрос без бюджета и без типа → вопрос 'both'."""
        params = {
            "search_queries": ["guitar"],
            "price_min": None,
            "price_max": None,
        }
        result = check_needs_clarification(params)
        assert result is not None
        assert "бюджет" in result.lower()
        assert "тип" in result.lower()

    def test_no_budget_returns_budget_question(self):
        """Запрос с типом но без бюджета → вопрос 'budget'."""
        params = {
            "search_queries": ["Fender Stratocaster"],
            "price_min": None,
            "price_max": None,
            "type": "Stratocaster",
        }
        result = check_needs_clarification(params)
        assert result is not None
        assert "бюджет" in result.lower()
        assert "тип" not in result.lower() or "тип гитары" not in result.lower()

    def test_no_type_returns_type_question(self):
        """Запрос с бюджетом но без типа → вопрос 'type'."""
        params = {
            "search_queries": ["guitar"],
            "price_min": None,
            "price_max": 500,
        }
        result = check_needs_clarification(params)
        assert result is not None
        assert "тип" in result.lower()

    def test_all_params_present_returns_none(self):
        """Все параметры есть → None (уточнение не нужно)."""
        params = {
            "search_queries": ["Fender Stratocaster"],
            "price_min": None,
            "price_max": 500,
            "type": "Stratocaster",
            "pickups": "SSS",
            "brand": "Fender",
        }
        result = check_needs_clarification(params)
        assert result is None

    def test_empty_search_queries_returns_type_question(self):
        """Пустые search_queries → вопрос о типе."""
        params = {
            "search_queries": [],
            "price_min": None,
            "price_max": 500,
            "type": "Stratocaster",
        }
        result = check_needs_clarification(params)
        assert result is not None
        assert "тип" in result.lower()

    def test_budget_zero_treated_as_no_budget(self):
        """Бюджет = 0 считается как отсутствующий."""
        params = {
            "search_queries": ["guitar"],
            "price_min": None,
            "price_max": 0,
            "type": "Stratocaster",
        }
        result = check_needs_clarification(params)
        assert result is not None
        assert "бюджет" in result.lower()

    def test_empty_string_type_treated_as_no_type(self):
        """Пустая строка типа считается как отсутствующий тип."""
        params = {
            "search_queries": ["guitar"],
            "price_min": None,
            "price_max": 500,
            "type": "",
        }
        result = check_needs_clarification(params)
        assert result is not None
        assert "тип" in result.lower()

    def test_params_with_price_max_key(self):
        """Поддержка ключа 'price_max' (альтернатива 'budget_max')."""
        params = {
            "search_queries": ["Fender"],
            "price_min": None,
            "price_max": 800,
            "type": "Telecaster",
        }
        result = check_needs_clarification(params)
        # Есть бюджет и тип, но search_queries есть → должен работать
        # Если search_queries не пустой → None
        assert result is None

    def test_empty_dict_returns_both_question(self):
        """Пустой dict → вопрос 'both'."""
        params = {}
        result = check_needs_clarification(params)
        assert result is not None
        assert "бюджет" in result.lower()
        assert "тип" in result.lower()
