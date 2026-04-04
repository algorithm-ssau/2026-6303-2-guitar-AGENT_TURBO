"""
Тесты для очистки ranking модуля (Неделя 4).

Проверяют:
- Результаты не содержат score/_score
- Ранжирование работает с минимальными параметрами
- Гитара в бюджете с совпадением в title → выше
"""

from backend.ranking.ranking import rank_results


def test_no_score_in_output():
    """Результаты не содержат score/_score."""
    results = [
        {"title": "Fender Strat", "price": 500, "score": 85, "_score": 85},
        {"title": "Gibson Les Paul", "price": 800},
    ]
    params = {"budget_max": 600, "search_queries": ["strat"]}
    ranked = rank_results(results, params)

    assert len(ranked) == 2
    for r in ranked:
        assert "score" not in r, f"score поле не должно быть в результате: {r}"
        assert "_score" not in r, f"_score поле не должно быть в результате: {r}"


def test_minimal_params_ranking():
    """Минимальные параметры (budget_max + search_queries) → ранжирование работает."""
    results = [
        {"title": "Fender Stratocaster", "price": 450},
        {"title": "Gibson Les Paul", "price": 800},
    ]
    params = {"budget_max": 500, "search_queries": ["strat"]}
    ranked = rank_results(results, params)

    assert len(ranked) == 2
    # Fender Stratocaster должен быть первым: в бюджете + совпадение в title
    assert ranked[0]["title"] == "Fender Stratocaster"


def test_budget_and_title_priority():
    """Гитара в бюджете с совпадением в title → выше чем без совпадения."""
    results = [
        {"title": "Gibson Les Paul", "price": 900},  # не в бюджете, нет совпадения
        {"title": "Fender Stratocaster", "price": 450},  # в бюджете + совпадение
    ]
    params = {"budget_max": 500, "search_queries": ["strat"]}
    ranked = rank_results(results, params)

    assert ranked[0]["title"] == "Fender Stratocaster"
    assert ranked[1]["title"] == "Gibson Les Paul"


def test_empty_results():
    """Пустой список → пустой результат."""
    results = []
    params = {"budget_max": 500, "search_queries": ["strat"]}
    ranked = rank_results(results, params)

    assert ranked == []


def test_single_result():
    """Один результат → возвращается как есть."""
    results = [{"title": "Fender Strat", "price": 500}]
    params = {"budget_max": 600, "search_queries": ["strat"]}
    ranked = rank_results(results, params)

    assert len(ranked) == 1
    assert ranked[0]["title"] == "Fender Strat"
    assert "score" not in ranked[0]
    assert "_score" not in ranked[0]


def test_top_5_limit():
    """Возвращается максимум 5 результатов."""
    results = [
        {"title": f"Guitar {i}", "price": 100 * i}
        for i in range(1, 11)  # 10 результатов
    ]
    params = {"budget_max": 500, "search_queries": ["guitar"]}
    ranked = rank_results(results, params)

    assert len(ranked) <= 5


def test_score_cleaned_even_if_present():
    """score/_score удаляются даже если они были в исходных данных."""
    results = [
        {"title": "Fender Strat", "price": 400, "score": 99, "_score": 99},
        {"title": "Squier Strat", "price": 300, "score": 88, "_score": 88},
    ]
    params = {"budget_max": 500, "search_queries": ["strat"]}
    ranked = rank_results(results, params)

    for r in ranked:
        assert "score" not in r
        assert "_score" not in r
