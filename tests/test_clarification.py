"""Тесты модуля уточняющих вопросов (clarification)."""

import pytest
from backend.agent.clarification import check_needs_clarification


class TestCheckNeedsClarification:
    """Тесты функции check_needs_clarification."""

    def test_no_budget_no_type_returns_both_question(self):
        """Совсем пустой запрос без критериев должен вызывать уточнение."""
        params = {
            "search_queries": [],
            "price_min": None,
            "price_max": None,
        }
        result = check_needs_clarification(params)
        assert result is not None
        assert "бюджет" in result.lower()
        assert "тип" in result.lower()

    def test_no_budget_returns_none_when_type_present(self):
        """Тип без бюджета уже достаточен для широкого поиска."""
        params = {
            "search_queries": ["Fender Stratocaster"],
            "price_min": None,
            "price_max": None,
            "type": "Stratocaster",
        }
        result = check_needs_clarification(params)
        assert result is None

    def test_no_type_returns_none_when_budget_present(self):
        """Бюджет без типа уже достаточен для широкого поиска."""
        params = {
            "search_queries": ["guitar"],
            "price_min": None,
            "price_max": 500,
        }
        result = check_needs_clarification(params)
        assert result is None

    def test_specific_query_and_budget_do_not_require_type(self):
        """Если search_queries уже содержат конкретную форму/модель, уточнение типа не нужно."""
        params = {
            "search_queries": ["Fender Stratocaster"],
            "price_min": None,
            "price_max": 1200,
        }
        result = check_needs_clarification(params)
        assert result is None

    def test_single_known_shape_and_budget_do_not_require_type(self):
        """Даже один известный тип в query должен быть достаточен для поиска."""
        params = {
            "search_queries": ["Stratocaster"],
            "price_min": None,
            "price_max": 1200,
        }
        result = check_needs_clarification(params)
        assert result is None

    def test_any_type_with_budget_and_query_does_not_require_type(self):
        """Если пользователь явно сказал 'любой тип', повторно спрашивать тип нельзя."""
        params = {
            "search_queries": ["electric guitar"],
            "price_min": None,
            "price_max": 600,
            "type": "не важно",
        }
        result = check_needs_clarification(params)
        assert result is None

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

    def test_empty_search_queries_with_type_still_searchable(self):
        """Даже без search_queries типа достаточно, query достроится позже."""
        params = {
            "search_queries": [],
            "price_min": None,
            "price_max": 500,
            "type": "Stratocaster",
        }
        result = check_needs_clarification(params)
        assert result is None

    def test_budget_zero_treated_as_no_budget_but_type_is_enough(self):
        """Даже если budget=0, одного типа уже достаточно для поиска."""
        params = {
            "search_queries": ["guitar"],
            "price_min": None,
            "price_max": 0,
            "type": "Stratocaster",
        }
        result = check_needs_clarification(params)
        assert result is None

    def test_empty_string_type_with_budget_is_still_searchable(self):
        """Пустой type при наличии бюджета не должен блокировать поиск."""
        params = {
            "search_queries": ["guitar"],
            "price_min": None,
            "price_max": 500,
            "type": "",
        }
        result = check_needs_clarification(params)
        assert result is None

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

    def test_sound_only_is_enough_for_search(self):
        """Один только sound тоже должен запускать широкий поиск."""
        params = {
            "search_queries": [],
            "price_max": None,
            "sound": "bright",
        }
        result = check_needs_clarification(params)
        assert result is None
