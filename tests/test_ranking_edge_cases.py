"""
Тесты на граничные случаи для модуля ранжирования.
Минимум 7 тестов.
"""

import pytest
from backend.ranking.ranking import rank_results, score_budget, score_title


class TestRankingEdgeCases:
    """Тесты на граничные случаи."""

    def test_no_budget_neutral_score(self):
        """Тест 1: Без бюджета → нейтральный budget score (50)."""
        result = {'title': 'Guitar', 'price': 1000}
        params = {}  # price_max отсутствует

        budget_score = score_budget(result, params)

        assert budget_score == 50.0

    def test_single_result_returns_as_is(self):
        """Тест 2: Один результат → возвращается как есть."""
        mock_results = [
            {'title': 'Single Guitar', 'price': 500},
        ]
        params = {'price_max': 600}

        results = rank_results(mock_results, params)

        assert len(results) == 1
        assert results[0]['title'] == 'Single Guitar'

    def test_all_prices_above_budget_still_returns(self):
        """Тест 3: Все цены выше бюджета → результаты всё равно возвращаются."""
        mock_results = [
            {'title': 'Expensive 1', 'price': 2000},
            {'title': 'Expensive 2', 'price': 3000},
        ]
        params = {'price_max': 500}

        results = rank_results(mock_results, params)

        assert len(results) == 2  # результаты возвращены несмотря на превышение

    def test_negative_price_doesnt_break(self):
        """Тест 4: Отрицательная цена → не ломается."""
        mock_results = [
            {'title': 'Negative Price', 'price': -100},
        ]
        params = {'price_max': 500}

        results = rank_results(mock_results, params)

        assert len(results) == 1  # не падает с ошибкой

    def test_score_not_in_output(self):
        """Тест 5: _score не в output."""
        mock_results = [
            {'title': 'Guitar', 'price': 500},
        ]
        params = {'price_max': 600}

        results = rank_results(mock_results, params)

        assert '_score' not in results[0]
        assert 'score' not in results[0]

    def test_no_search_queries_neutral_title_score(self):
        """Тест 6: Без search_queries → нейтральный title score (0)."""
        result = {'title': 'Fender Stratocaster'}
        params = {}  # search_queries отсутствует

        title_score = score_title(result, params)

        assert title_score == 0.0

    def test_exact_phrase_match_max_score(self):
        """Тест 7: Точное совпадение фразы → максимальный score (100)."""
        result = {'title': 'Fender Stratocaster'}
        params = {'search_queries': 'stratocaster'}

        title_score = score_title(result, params)

        assert title_score == 100.0
