"""
Тесты для модуля ранжирования результатов поиска гитар.
"""

import pytest
from backend.ranking.ranking import rank_results, calculate_total_score


class TestRankResultsBasic:
    """Базовые тесты функции rank_results."""
    
    def test_rank_results_returns_top_5(self):
        """Тест: функция возвращает ровно 5 лучших результатов из 10."""
        mock_results = [
            {'title': 'Guitar 1', 'price': 450, 'type': 'Stratocaster', 'pickups': 'SSS',
             'brand': 'Squier', 'condition': 'New', 'country': 'China'},
            {'title': 'Guitar 2', 'price': 850, 'type': 'Stratocaster', 'pickups': 'SSS',
             'brand': 'Fender', 'condition': 'New', 'country': 'Mexico'},
            {'title': 'Guitar 3', 'price': 300, 'type': 'Stratocaster', 'pickups': 'HSS',
             'brand': 'Yamaha', 'condition': 'New', 'country': 'Indonesia'},
            {'title': 'Guitar 4', 'price': 1200, 'type': 'Stratocaster', 'pickups': 'HSS',
             'brand': 'Ibanez', 'condition': 'New', 'country': 'Indonesia'},
            {'title': 'Guitar 5', 'price': 550, 'type': 'Les Paul', 'pickups': 'HH',
             'brand': 'Epiphone', 'condition': 'New', 'country': 'China'},
            {'title': 'Guitar 6', 'price': 400, 'type': 'Stratocaster', 'pickups': 'SSS',
             'brand': 'Squier', 'condition': 'New', 'country': 'India'},
            {'title': 'Guitar 7', 'price': 950, 'type': 'Telecaster', 'pickups': 'S',
             'brand': 'Fender', 'condition': 'New', 'country': 'Mexico'},
            {'title': 'Guitar 8', 'price': 750, 'type': 'Telecaster', 'pickups': 'S',
             'brand': 'G&L', 'condition': 'New', 'country': 'USA'},
            {'title': 'Guitar 9', 'price': 230, 'type': 'Telecaster', 'pickups': 'S',
             'brand': 'Squier', 'condition': 'New', 'country': 'India'},
            {'title': 'Guitar 10', 'price': 150, 'type': 'Telecaster', 'pickups': 'S',
             'brand': 'Harley Benton', 'condition': 'New', 'country': 'China'},
        ]
        
        params = {
            'budget_max': 500,
            'type': 'Stratocaster',
            'pickups': 'SSS'
        }
        
        top_5 = rank_results(mock_results, params)
        
        # Проверяем что вернулось ровно 5 результатов
        assert len(top_5) == 5
        
        # Проверяем что все результаты имеют поле score
        for result in top_5:
            assert 'score' in result
        
        # Проверяем что результаты отсортированы по убыванию score
        for i in range(len(top_5) - 1):
            assert top_5[i]['score'] >= top_5[i + 1]['score']
    
    def test_rank_results_correct_order_stratocaster(self):
        """Тест: правильный порядок для запроса Stratocaster с бюджетом до $500.
        
        Ожидаемый порядок (из docs/RANKING.md):
        1. Squier Classic Vibe Strat (89.0) — в бюджете, правильный тип и датчики
        2. Yamaha Pacifica 112V (86.5) — в бюджете, похожий звук (HSS)
        3. Fender Player Stratocaster (79.0) — превышает бюджет, но премиум бренд
        """
        mock_results = [
            {'title': 'Fender Player Stratocaster', 'price': 850, 'type': 'Stratocaster',
             'pickups': 'SSS', 'brand': 'Fender', 'condition': 'New', 'country': 'Mexico'},
            {'title': 'Squier Classic Vibe Strat', 'price': 450, 'type': 'Stratocaster',
             'pickups': 'SSS', 'brand': 'Squier', 'condition': 'New', 'country': 'China'},
            {'title': 'Yamaha Pacifica 112V', 'price': 300, 'type': 'Stratocaster',
             'pickups': 'HSS', 'brand': 'Yamaha', 'condition': 'New', 'country': 'Indonesia'},
            {'title': 'Ibanez AZ224F', 'price': 1200, 'type': 'Stratocaster',
             'pickups': 'HSS', 'brand': 'Ibanez', 'condition': 'New', 'country': 'Indonesia'},
            {'title': 'Epiphone Les Paul Standard', 'price': 550, 'type': 'Les Paul',
             'pickups': 'HH', 'brand': 'Epiphone', 'condition': 'New', 'country': 'China'},
        ]
        
        params = {
            'budget_max': 500,
            'type': 'Stratocaster',
            'pickups': 'SSS'
        }
        
        top_5 = rank_results(mock_results, params)
        
        # Squier должен быть первым (лучшее совпадение по бюджету и параметрам)
        assert top_5[0]['title'] == 'Squier Classic Vibe Strat'
        
        # Yamaha должна быть второй (в бюджете, но HSS вместо SSS)
        assert top_5[1]['title'] == 'Yamaha Pacifica 112V'
        
        # Fender должен быть третьим (превышает бюджет, но премиум бренд)
        assert top_5[2]['title'] == 'Fender Player Stratocaster'
        
        # Les Paul должен быть последним (не тот тип и датчики)
        assert top_5[-1]['title'] == 'Epiphone Les Paul Standard'
    
    def test_score_calculation_stratocaster_example(self):
        """Тест: проверка расчёта score на примере из документации.
        
        Squier Classic Vibe Strat ($450, Stratocaster, SSS, Squier, New, China):
        - Бюджет (30%): 100 (в бюджете)
        - Тип (25%): 100 (точное совпадение)
        - Датчики (20%): 100 (точное совпадение)
        - Бренд (10%): 60 (средний сегмент)
        - Состояние (10%): 100 (new)
        - Страна (5%): 60 (China)
        Итого: 100*0.30 + 100*0.25 + 100*0.20 + 60*0.10 + 100*0.10 + 60*0.05 = 94.0
        """
        result = {
            'title': 'Squier Classic Vibe Strat',
            'price': 450,
            'type': 'Stratocaster',
            'pickups': 'SSS',
            'brand': 'Squier',
            'condition': 'New',
            'country': 'China'
        }
        
        params = {
            'budget_max': 500,
            'type': 'Stratocaster',
            'pickups': 'SSS'
        }
        
        score = calculate_total_score(result, params)
        
        # Ожидаемый score: 94.0
        assert score == 94.0
    
    def test_score_calculation_fender_player(self):
        """Тест: проверка расчёта score для Fender Player Stratocaster.
        
        Fender Player Stratocaster ($850, Stratocaster, SSS, Fender, New, Mexico):
        - Бюджет (30%): 0 (превышает на 70%, это > 20%)
        - Тип (25%): 100 (точное совпадение)
        - Датчики (20%): 100 (точное совпадение)
        - Бренд (10%): 80 (премиум)
        - Состояние (10%): 100 (new)
        - Страна (5%): 80 (Mexico)
        Итого: 0*0.30 + 100*0.25 + 100*0.20 + 80*0.10 + 100*0.10 + 80*0.05 = 67.0
        """
        result = {
            'title': 'Fender Player Stratocaster',
            'price': 850,
            'type': 'Stratocaster',
            'pickups': 'SSS',
            'brand': 'Fender',
            'condition': 'New',
            'country': 'Mexico'
        }
        
        params = {
            'budget_max': 500,
            'type': 'Stratocaster',
            'pickups': 'SSS'
        }
        
        score = calculate_total_score(result, params)
        
        # Ожидаемый score: 67.0
        assert score == 67.0
    
    def test_score_calculation_yamaha_pacifica(self):
        """Тест: проверка расчёта score для Yamaha Pacifica 112V.
        
        Yamaha Pacifica 112V ($300, Stratocaster, HSS, Yamaha, New, Indonesia):
        - Бюджет (30%): 100 (в бюджете)
        - Тип (25%): 100 (точное совпадение)
        - Датчики (20%): 70 (HSS — частично похоже на SSS)
        - Бренд (10%): 60 (средний сегмент)
        - Состояние (10%): 100 (new)
        - Страна (5%): 70 (Indonesia)
        Итого: 100*0.30 + 100*0.25 + 70*0.20 + 60*0.10 + 100*0.10 + 70*0.05 = 88.5
        """
        result = {
            'title': 'Yamaha Pacifica 112V',
            'price': 300,
            'type': 'Stratocaster',
            'pickups': 'HSS',
            'brand': 'Yamaha',
            'condition': 'New',
            'country': 'Indonesia'
        }
        
        params = {
            'budget_max': 500,
            'type': 'Stratocaster',
            'pickups': 'SSS'
        }
        
        score = calculate_total_score(result, params)
        
        # Ожидаемый score: 88.5
        assert score == 88.5
    
    def test_telecaster_country_priority(self):
        """Тест: приоритет страны производства для запроса Telecaster.
        
        G&L ASAT Classic ($750, Telecaster, S, G&L, New, USA):
        - Бюджет (30%): 100 (в бюджете до $800)
        - Тип (25%): 100 (точное совпадение)
        - Датчики (20%): 100 (single coil)
        - Бренд (10%): 80 (G&L — известный бренд)
        - Состояние (10%): 100 (new)
        - Страна (5%): 100 (USA — высший приоритет)
        Итого: 100*0.30 + 100*0.25 + 100*0.20 + 80*0.10 + 100*0.10 + 100*0.05 = 98.0
        """
        result = {
            'title': 'G&L ASAT Classic',
            'price': 750,
            'type': 'Telecaster',
            'pickups': 'S',
            'brand': 'G&L',
            'condition': 'New',
            'country': 'USA'
        }
        
        params = {
            'budget_max': 800,
            'type': 'Telecaster',
            'pickups': 'S',
            'country': 'USA'
        }
        
        score = calculate_total_score(result, params)
        
        # Ожидаемый score: 98.0 (USA совпадает с запросом)
        assert score == 98.0
    
    def test_humbucker_vs_single_coil_opposite(self):
        """Тест: противоположные характеры датчиков получают 0.
        
        Запрос: single coil (SSS)
        Результат: humbucker (HH)
        Ожидаемый score за датчики: 0
        """
        result = {
            'title': 'Gibson Les Paul',
            'price': 1500,
            'type': 'Les Paul',
            'pickups': 'HH',
            'brand': 'Gibson',
            'condition': 'New',
            'country': 'USA'
        }
        
        params = {
            'budget_max': 2000,
            'type': 'Stratocaster',
            'pickups': 'SSS'  # single coil
        }

        # Проверяем что score за датчики = 0
        from backend.ranking.ranking import score_pickups
        pickups_score = score_pickups(result, params)

        assert pickups_score == 0.0


class TestRankResultsEdgeCases:
    """Тесты на граничные случаи для функции rank_results."""

    def test_rank_results_empty_list(self):
        """Тест 1: пустой список на входе."""
        mock_results = []
        params = {
            'budget_max': 500,
            'type': 'Stratocaster',
            'pickups': 'SSS'
        }

        results = rank_results(mock_results, params)

        assert results == []

    def test_rank_results_equal_scores(self):
        """Тест 2: все результаты с одинаковым скором."""
        mock_results = [
            {
                'title': 'Guitar 1',
                'price': 400,
                'type': 'Stratocaster',
                'pickups': 'SSS',
                'brand': 'Squier',
                'condition': 'New',
                'country': 'China'
            },
            {
                'title': 'Guitar 2',
                'price': 400,
                'type': 'Stratocaster',
                'pickups': 'SSS',
                'brand': 'Squier',
                'condition': 'New',
                'country': 'China'
            },
            {
                'title': 'Guitar 3',
                'price': 400,
                'type': 'Stratocaster',
                'pickups': 'SSS',
                'brand': 'Squier',
                'condition': 'New',
                'country': 'China'
            },
        ]

        params = {
            'budget_max': 500,
            'type': 'Stratocaster',
            'pickups': 'SSS'
        }

        results = rank_results(mock_results, params)

        # Все результаты должны быть (3 штуки, все ≤ 5)
        assert len(results) == 3
        # Все scores должны быть равны
        first_score = results[0]['score']
        for result in results:
            assert result['score'] == first_score

    def test_rank_results_no_budget(self):
        """Тест 3: бюджет не указан в params."""
        mock_results = [
            {
                'title': 'Cheap Guitar',
                'price': 100,
                'type': 'Stratocaster',
                'pickups': 'SSS',
                'brand': 'Harley Benton',
                'condition': 'New',
                'country': 'China'
            },
            {
                'title': 'Expensive Guitar',
                'price': 2000,
                'type': 'Stratocaster',
                'pickups': 'SSS',
                'brand': 'Fender',
                'condition': 'New',
                'country': 'USA'
            },
            {
                'title': 'Medium Guitar',
                'price': 500,
                'type': 'Stratocaster',
                'pickups': 'SSS',
                'brand': 'Yamaha',
                'condition': 'New',
                'country': 'Indonesia'
            },
        ]

        # budget_max отсутствует
        params = {
            'type': 'Stratocaster',
            'pickups': 'SSS'
        }

        results = rank_results(mock_results, params)

        # Все результаты должны быть (без фильтра по бюджету)
        assert len(results) == 3
        # Fender должен быть выше из-за премиум бренда и USA
        assert results[0]['brand'] == 'Fender'

    def test_rank_results_type_mismatch(self):
        """Тест 4: тип инструмента не совпадает ни с одним результатом."""
        mock_results = [
            {
                'title': 'Les Paul Standard',
                'price': 800,
                'type': 'Les Paul',
                'pickups': 'HH',
                'brand': 'Gibson',
                'condition': 'New',
                'country': 'USA'
            },
            {
                'title': 'SG Standard',
                'price': 700,
                'type': 'SG',
                'pickups': 'HH',
                'brand': 'Gibson',
                'condition': 'New',
                'country': 'USA'
            },
            {
                'title': 'ES-335',
                'price': 900,
                'type': 'ES-335',
                'pickups': 'HH',
                'brand': 'Epiphone',
                'condition': 'New',
                'country': 'China'
            },
        ]

        params = {
            'budget_max': 1000,
            'type': 'Stratocaster',  # Запрошен Stratocaster, но в результатах нет
            'pickups': 'SSS'
        }

        results = rank_results(mock_results, params)

        # Все результаты должны быть (просто с низкими scores за тип)
        assert len(results) == 3
        # Все scores должны быть относительно низкими из-за несовпадения типа
        # (тип даёт 25% веса, при 0 баллов это снижает общий score)
        for result in results:
            # Максимальный возможный score без типа: 75 баллов (остальные критерии)
            # Но с учётом весов: 0*0.25 + 100*0.75 = 75
            assert result['score'] < 80  # меньше чем если бы тип совпал
