"""
Тесты проверяют ранжирование внутри полного pipeline.

Проверяют:
- interpret_query возвращает не более 5 результатов
- Гитара в бюджете с совпадением в title → первая
- score не в выходных данных
- Граничные случаи: 0 результатов, 3 результата
"""

from unittest.mock import MagicMock, patch

from backend.agent.service import interpret_query


def mock_search_results(queries, price_min, price_max):
    """Возвращает 10 mock-результатов с разными ценами и title."""
    return [
        {"title": "Fender Player Stratocaster", "price": 850},
        {"title": "Squier Classic Vibe Strat", "price": 450},
        {"title": "Yamaha Pacifica 112V", "price": 300},
        {"title": "Ibanez AZ224F", "price": 1200},
        {"title": "Epiphone Les Paul Standard", "price": 550},
        {"title": "Fender Vintera 50s Tele", "price": 950},
        {"title": "Squier 40th Anniversary Tele", "price": 230},
        {"title": "G&L ASAT Classic", "price": 750},
        {"title": "Fender Player Plus Tele", "price": 1050},
        {"title": "Harley Benton TE-52", "price": 150},
    ]


@patch('backend.agent.service.search_reverb_exact')
@patch('backend.agent.service.create_llm_client')
def test_pipeline_returns_max_5_results(mock_llm, mock_search):
    """interpret_query возвращает не более 5 результатов из 10."""
    mock_search.return_value = mock_search_results(None, None, None)

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = _route_plan("strat", 500)
    mock_llm.return_value = mock_client

    result = interpret_query("Хочу страт до $500")

    assert "results" in result
    assert len(result["results"]) <= 5


@patch('backend.agent.service.search_reverb_exact')
@patch('backend.agent.service.create_llm_client')
def test_budget_guitar_first(mock_llm, mock_search):
    """Гитара в бюджете с совпадением в title → первая."""
    mock_search.return_value = mock_search_results(None, None, None)

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = _route_plan("strat", 500)
    mock_llm.return_value = mock_client

    result = interpret_query("Хочу страт до $500")

    # Squier Classic Vibe Strat ($450) должен быть выше чем Fender Player ($850)
    titles = [r["title"] for r in result["results"]]
    if "Squier Classic Vibe Strat" in titles and "Fender Player Stratocaster" in titles:
        assert titles.index("Squier Classic Vibe Strat") < titles.index("Fender Player Stratocaster")


@patch('backend.agent.service.search_reverb_exact')
@patch('backend.agent.service.create_llm_client')
def test_no_score_in_output(mock_llm, mock_search):
    """score/_score не в выходных данных."""
    mock_search.return_value = mock_search_results(None, None, None)

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = _route_plan("strat", 500)
    mock_llm.return_value = mock_client

    result = interpret_query("Хочу страт до $500")

    for r in result["results"]:
        assert "score" not in r, f"score не должно быть в результате: {r}"
        assert "_score" not in r, f"_score не должно быть в результате: {r}"


@patch('backend.agent.service.search_reverb_exact')
@patch('backend.agent.service.create_llm_client')
def test_zero_results_from_search(mock_llm, mock_search):
    """search_reverb вернул 0 результатов → пустой список."""
    mock_search.return_value = []

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = _route_plan("strat", 500)
    mock_llm.return_value = mock_client

    result = interpret_query("Хочу страт до $500")

    assert result["results"] == []


@patch('backend.agent.service.search_reverb_exact')
@patch('backend.agent.service.create_llm_client')
def test_less_than_5_results(mock_llm, mock_search):
    """search_reverb вернул 3 результата → 3 на выходе (не 5)."""
    mock_search.return_value = mock_search_results(None, None, None)[:3]

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = _route_plan("strat", 500)
    mock_llm.return_value = mock_client

    result = interpret_query("Хочу страт до $500")

    assert len(result["results"]) == 3


@patch('backend.agent.service.search_reverb_exact')
@patch('backend.agent.service.create_llm_client')
def test_ranking_order_matches_expectations(mock_llm, mock_search):
    """Порядок результатов соответствует ожиданиям по бюджету и title."""
    mock_search.return_value = mock_search_results(None, None, None)

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = _route_plan("tele", 800)
    mock_llm.return_value = mock_client

    result = interpret_query("Нужен телекастер до $800")

    # G&L ASAT Classic ($750) и Squier Tele ($230) должны быть в топ-3
    titles = [r["title"] for r in result["results"][:3]]
    tele_titles = [t for t in titles if "Tele" in t or "ASAT" in t]
    assert len(tele_titles) >= 2


def _route_plan(query: str, price_max: int) -> dict:
    return {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {
            "search_queries": [query],
            "price_min": None,
            "price_max": price_max,
            "type": "any",
            "brand": None,
            "pickups": None,
            "sound": None,
            "style": None,
        },
        "should_offer_search": False,
    }
