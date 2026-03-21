"""Тесты логики интерпретации запроса (service.py) с использованием мока Groq-клиента."""

import pytest
from unittest.mock import MagicMock
from backend.agent.service import interpret_query

def test_interpret_query_search_mode():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"mode": "search", "params": {"search_queries": ["Jackson JS22"], "price_max": 450}}'
    mock_client.chat.completions.create.return_value = mock_response

    result = interpret_query("Нужна гитара для металла до 45к", llm_client=mock_client)
    assert result["mode"] == "search"
    assert "params" in result
    assert "search_queries" in result["params"]
    assert result["params"]["price_max"] == 450

def test_interpret_query_consultation_mode():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"mode": "consultation", "answer": "Синглы звучат ярче."}'
    mock_client.chat.completions.create.return_value = mock_response

    result = interpret_query("Чем отличаются синглы?", llm_client=mock_client)
    assert result["mode"] == "consultation"
    assert result["answer"] == "Синглы звучат ярче."

def test_interpret_query_invalid_json():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    result = interpret_query("Привет", llm_client=mock_client)
    assert result["mode"] == "consultation"
    assert "Извините, произошла ошибка" in result["answer"]
