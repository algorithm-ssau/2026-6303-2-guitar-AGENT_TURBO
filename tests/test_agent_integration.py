"""Тесты интеграции: проверяем что ветки search/consultation работают корректно."""

from unittest.mock import MagicMock

from backend.agent.service import interpret_query


def test_consultation_does_not_call_search():
    """При consultation-запросе поиск НЕ вызывается, LLM отвечает напрямую."""
    mock_llm = MagicMock(return_value="Single-coil звучит ярче, humbucker — теплее.")
    mock_search = MagicMock(return_value=[])

    result = interpret_query(
        "В чем разница между single-coil и humbucker?",
        llm_client=mock_llm,
        search_fn=mock_search,
    )

    assert result["mode"] == "consultation"
    assert result["answer"] == "Single-coil звучит ярче, humbucker — теплее."
    mock_llm.assert_called_once()
    mock_search.assert_not_called()


def test_search_calls_search_fn():
    """При search-запросе вызывается функция поиска."""
    mock_llm = MagicMock(return_value="")
    mock_search = MagicMock(return_value=[{"title": "Fender Strat", "price": 800}])

    result = interpret_query(
        "Подбери электрогитару до 1200$ для блюза.",
        llm_client=mock_llm,
        search_fn=mock_search,
    )

    assert result["mode"] == "search"
    assert len(result["results"]) == 1
    mock_search.assert_called_once()
    mock_llm.assert_not_called()
