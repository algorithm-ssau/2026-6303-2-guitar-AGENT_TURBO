"""
Тесты для модуля ранжирования (упрощённая версия).
Формула: бюджет (55%) + название (45%)
"""

import pytest
from backend.ranking.ranking import rank_results, score_budget, score_title, score_sound, score_style


class TestRankResults:
    """Базовые тесты функции rank_results."""

    def test_returns_top_5_from_10(self):
        """Тест 1: 10 результатов → 5 на выходе."""
        mock_results = [
            {'title': 'Fender Stratocaster', 'price': 450},
            {'title': 'Gibson Les Paul', 'price': 1200},
            {'title': 'Squier Telecaster', 'price': 230},
            {'title': 'Yamaha Pacifica', 'price': 300},
            {'title': 'Ibanez RG', 'price': 800},
            {'title': 'Epiphone SG', 'price': 350},
            {'title': 'Fender Telecaster', 'price': 950},
            {'title': 'Gibson SG', 'price': 1100},
            {'title': 'PRS Custom 24', 'price': 2500},
            {'title': 'Harley Benton ST', 'price': 150},
        ]

        params = {
            'price_max': 500,
            'search_queries': 'stratocaster'
        }

        top_5 = rank_results(mock_results, params)

        assert len(top_5) == 5

    def test_budget_in_range_ranks_higher(self):
        """Тест 2: Гитара в бюджете ранжируется выше дорогой."""
        mock_results = [
            {'title': 'Cheap Guitar', 'price': 400},
            {'title': 'Expensive Guitar', 'price': 1000},
        ]

        params = {'price_max': 500}

        top_5 = rank_results(mock_results, params)

        assert top_5[0]['title'] == 'Cheap Guitar'
        assert top_5[1]['title'] == 'Expensive Guitar'

    def test_title_match_improves_position(self):
        """Тест 3: Совпадение по названию повышает позицию."""
        mock_results = [
            {'title': 'Fender Stratocaster', 'price': 600},  # в бюджете × 1.2
            {'title': 'Yamaha Pacifica', 'price': 450},  # в бюджете, но нет совпадения
        ]

        params = {
            'price_max': 500,
            'search_queries': 'stratocaster'
        }

        top_5 = rank_results(mock_results, params)

        # Stratocaster должен быть выше из-за совпадения названия
        assert top_5[0]['title'] == 'Fender Stratocaster'

    def test_empty_list_returns_empty(self):
        """Тест 4: Пустой список → пустой результат."""
        mock_results = []
        params = {'price_max': 500}

        results = rank_results(mock_results, params)

        assert results == []

    def test_score_not_in_output(self):
        """Тест 5: _score не в output."""
        mock_results = [
            {'title': 'Fender Stratocaster', 'price': 450},
        ]

        params = {'price_max': 500}

        results = rank_results(mock_results, params)

        assert '_score' not in results[0]
        assert 'score' not in results[0]  # тоже не должно быть


class TestScoreBudget:
    """Тесты для score_budget."""

    def test_price_in_budget(self):
        """Цена в бюджете → 100."""
        result = {'price': 400}
        params = {'price_max': 500}

        assert score_budget(result, params) == 100.0

    def test_price_exceeds_up_to_20_percent(self):
        """Превышает до 20% → 50."""
        result = {'price': 550}  # 500 * 1.2 = 600
        params = {'price_max': 500}

        assert score_budget(result, params) == 50.0

    def test_price_exceeds_more_than_20_percent(self):
        """Превышает более 20% → 0."""
        result = {'price': 700}
        params = {'price_max': 500}

        assert score_budget(result, params) == 0.0

    def test_no_budget_specified(self):
        """Бюджет не указан → 50."""
        result = {'price': 400}
        params = {}

        assert score_budget(result, params) == 50.0


class TestScoreTitle:
    """Тесты для score_title."""

    def test_exact_phrase_match(self):
        """Полное совпадение фразы → 100."""
        result = {'title': 'Fender Stratocaster'}
        params = {'search_queries': 'stratocaster'}

        assert score_title(result, params) == 100.0

    def test_two_plus_words_match(self):
        """2+ слова из запроса → 70."""
        result = {'title': 'Fender American Professional Strat'}
        params = {'search_queries': 'fender stratocaster american'}

        assert score_title(result, params) == 70.0

    def test_one_word_match(self):
        """1 слово из запроса → 40."""
        result = {'title': 'Fender Telecaster'}
        params = {'search_queries': 'fender stratocaster'}

        assert score_title(result, params) == 40.0

    def test_no_match(self):
        """Нет совпадений → 0."""
        result = {'title': 'Gibson Les Paul'}
        params = {'search_queries': 'fender stratocaster'}

        assert score_title(result, params) == 0.0

    def test_no_search_queries(self):
        """search_queries не указан → 0."""
        result = {'title': 'Fender Stratocaster'}
        params = {}

        assert score_title(result, params) == 0.0


class TestSoundAndStyle:
    """Тесты эвристик sound/style."""

    def test_bright_sound_prefers_telecaster_and_strat(self):
        tele = {'title': 'Fender Telecaster SSS'}
        lp = {'title': 'Gibson Les Paul HH'}

        params = {'sound': 'bright'}

        assert score_sound(tele, params) > score_sound(lp, params)

    def test_metal_style_prefers_metal_friendly_models(self):
        metal = {'title': 'ESP LTD 7-string with EMG'}
        jazz = {'title': 'Epiphone Casino Semi-Hollow'}

        params = {'style': 'metal'}

        assert score_style(metal, params) > score_style(jazz, params)

    def test_rank_results_uses_sound_when_query_is_broad(self):
        mock_results = [
            {'title': 'Gibson Les Paul HH', 'price': 450},
            {'title': 'Fender Telecaster SSS', 'price': 450},
        ]

        params = {
            'price_max': 600,
            'search_queries': ['guitar'],
            'sound': 'bright',
        }

        ranked = rank_results(mock_results, params)

        assert ranked[0]['title'] == 'Fender Telecaster SSS'
