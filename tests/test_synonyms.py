"""Тесты модуля синонимов для поисковых запросов."""

import pytest

from backend.search.synonyms import SYNONYMS, expand_queries


class TestExpandQueries:
    """Тесты функции expand_queries."""

    def test_expand_strat_returns_stratocaster(self):
        """expand_queries(['strat']) → ['strat', 'stratocaster']."""
        result = expand_queries(["strat"])
        assert "strat" in result
        assert "stratocaster" in result
        assert len(result) == 2

    def test_expand_multiple_queries(self):
        """expand_queries(['LP', 'tele']) → содержит 'les paul' и 'telecaster'."""
        result = expand_queries(["LP", "tele"])
        assert "LP" in result
        assert "tele" in result
        assert "les paul" in result
        assert "telecaster" in result

    def test_empty_list_returns_empty(self):
        """expand_queries([]) → []."""
        assert expand_queries([]) == []

    def test_unknown_word_unchanged(self):
        """Неизвестное слово возвращается без изменений."""
        result = expand_queries(["xyz"])
        assert result == ["xyz"]

    def test_case_insensitive_lookup(self):
        """Поиск синонима регистронезависимый."""
        result = expand_queries(["STRAT"])
        assert "STRAT" in result
        assert "stratocaster" in result

    def test_no_duplicates_in_result(self):
        """Результат не содержит дубликатов."""
        result = expand_queries(["strat", "strat"])
        assert result.count("strat") == 1
        assert result.count("stratocaster") == 1

    def test_original_queries_preserved(self):
        """Исходные запросы сохраняются в результате."""
        result = expand_queries(["fender", "gibson"])
        assert "fender" in result
        assert "gibson" in result

    def test_mixed_known_and_unknown(self):
        """Смесь известных и неизвестных слов."""
        result = expand_queries(["strat", "custom"])
        assert "strat" in result
        assert "stratocaster" in result
        assert "custom" in result
        assert len(result) == 3


class TestSynonymsDict:
    """Тесты словаря SYNONYMS."""

    def test_minimum_20_entries(self):
        """Словарь содержит минимум 20 записей."""
        assert len(SYNONYMS) >= 20

    def test_has_russian_entries(self):
        """Словарь содержит русские записи (кириллица)."""
        has_ru = any(
            any(ord(c) > 127 for c in k) for k in SYNONYMS
        )
        assert has_ru

    def test_has_english_entries(self):
        """Словарь содержит английские записи."""
        has_en = any(
            all(ord(c) < 128 for c in k) for k in SYNONYMS
        )
        assert has_en

    def test_all_values_are_non_empty(self):
        """Все значения словаря — непустые строки."""
        for key, value in SYNONYMS.items():
            assert isinstance(key, str) and key.strip()
            assert isinstance(value, str) and value.strip()

    def test_no_self_references(self):
        """Ключ не равен своему значению."""
        for key, value in SYNONYMS.items():
            assert key.lower() != value.lower(), (
                f"Self-reference found: {key} -> {value}"
            )


class TestIntegration:
    """Интеграционные тесты: синонимы + поиск по мок-данным."""

    def test_strat_finds_stratocaster_in_mock(self):
        """Запрос 'strat' через пайплайн находит Stratocaster."""
        import os
        os.environ["USE_MOCK_REVERB"] = "true"

        from backend.search.search_reverb import search_reverb

        results = search_reverb(["strat"], price_max=1000)
        # Должен найти хотя бы один Stratocaster
        titles = [r["title"].lower() for r in results]
        assert any("stratocaster" in t for t in titles)

    def test_tele_finds_telecaster_in_mock(self):
        """Запрос 'tele' через пайплайн находит Telecaster."""
        import os
        os.environ["USE_MOCK_REVERB"] = "true"

        from backend.search.search_reverb import search_reverb

        results = search_reverb(["tele"], price_max=1000)
        titles = [r["title"].lower() for r in results]
        assert any("telecaster" in t for t in titles)

    def test_lp_finds_les_paul_in_mock(self):
        """Запрос 'LP' через пайплайн находит Les Paul."""
        import os
        os.environ["USE_MOCK_REVERB"] = "true"

        from backend.search.search_reverb import search_reverb

        results = search_reverb(["lp"], price_max=1200)
        titles = [r["title"].lower() for r in results]
        assert any("les paul" in t for t in titles)
