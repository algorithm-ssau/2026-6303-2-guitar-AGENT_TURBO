"""
Интеграционные тесты пайплайна поиска и ранжирования.

Тестирует полный цикл: загрузка mock-данных → фильтрация →
обогащение → ранжирование → топ-5.
"""

import pytest
from backend.search.service import search_and_rank


class TestSearchAndRankIntegration:
    """Интеграционные тесты пайплайна поиска с ранжированием."""

    def test_search_and_rank_returns_max_5_results(self):
        """Тест: пайплайн возвращает не более 5 результатов."""
        params = {
            'budget_max': 1000,
            'type': 'Stratocaster'
        }

        results = search_and_rank(params)

        assert len(results) <= 5

    def test_search_and_rank_results_have_score(self):
        """Тест: все результаты имеют поле score."""
        params = {
            'budget_max': 800,
            'type': 'Telecaster'
        }

        results = search_and_rank(params)

        assert len(results) > 0
        for result in results:
            assert 'score' in result

    def test_search_and_rank_results_sorted_by_score(self):
        """Тест: результаты отсортированы по убыванию score."""
        params = {
            'budget_max': 1000
        }

        results = search_and_rank(params)

        # Проверяем что результаты отсортированы по убыванию score
        for i in range(len(results) - 1):
            assert results[i]['score'] >= results[i + 1]['score']

    def test_search_and_rank_telecaster_single_coil(self):
        """Тест: запрос Telecaster с single coil датчиками.

        Ожидаемый порядок:
        1. Squier Classic Vibe Telecaster ($429) — в бюджете, правильный тип и датчики
        """
        params = {
            'budget_max': 800,
            'type': 'Telecaster',
            'pickups': 'S'
        }

        results = search_and_rank(params)

        # Проверяем что результаты есть
        assert len(results) > 0

        # Squier Telecaster должен быть первым (в бюджете, правильный тип и датчики)
        squier_tele = next((r for r in results if 'Squier' in r.get('brand', '') and 'Telecaster' in r.get('title', '')), None)
        assert squier_tele is not None
        
        # Squier Telecaster должен быть первым (highest score)
        assert results[0]['brand'] == 'Squier'

    def test_search_and_rank_budget_filter(self):
        """Тест: фильтрация по бюджету работает корректно."""
        params = {
            'budget_max': 400  # Только дешёвые гитары
        }

        results = search_and_rank(params)

        # Все результаты должны быть <= 400 * 1.2 = 480 (допускаем 20% превышение)
        for result in results:
            assert result['price'] <= 400 * 1.2

    def test_search_and_rank_parses_type_from_title(self):
        """Тест: тип гитары правильно извлекается из title."""
        params = {
            'budget_max': 1000,
            'type': 'Les Paul'
        }

        results = search_and_rank(params)

        # Gibson Les Paul должен быть в результатах и высоко ранжирован
        les_pauls = [r for r in results if r.get('type') == 'Les Paul']
        assert len(les_pauls) > 0

    def test_search_and_rank_parses_pickups_from_title(self):
        """Тест: конфигурация датчиков правильно извлекается из title."""
        params = {
            'budget_max': 1000,
            'pickups': 'HSS'
        }

        results = search_and_rank(params)

        # Fender Player Stratocaster HSS должен быть в результатах
        hss_guitars = [r for r in results if r.get('pickups') == 'HSS']
        assert len(hss_guitars) > 0

    def test_search_and_rank_empty_params(self):
        """Тест: пустые параметры возвращают все результаты отранжированные."""
        params = {}

        results = search_and_rank(params)

        # Должны вернуться результаты (не более 5)
        assert len(results) <= 5

        # Все должны иметь score
        for result in results:
            assert 'score' in result

    def test_search_and_rank_enriched_data(self):
        """Тест: данные обогащаются правильно (type, pickups, brand из title)."""
        params = {
            'budget_max': 1000
        }

        results = search_and_rank(params)

        # Проверяем что у всех результатов есть type, pickups, brand
        for result in results:
            # type может быть None если не найден в title
            assert 'type' in result
            # pickups может быть None если не найден в title
            assert 'pickups' in result
            # brand должен быть извлечён (большинство гитар имеют бренд в title)
            assert 'brand' in result
