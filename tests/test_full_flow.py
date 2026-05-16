import pytest
import os
from unittest.mock import MagicMock
from backend.agent.service import interpret_query

@pytest.fixture(autouse=True)
def setup_mock_env(monkeypatch):
    monkeypatch.setenv("USE_MOCK_REVERB", "true")

def test_full_flow_search(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    
    mock_llm = MagicMock()
    mock_llm.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {"search_queries": ["Fender"], "price_max": 1000, "type": "any"},
        "should_offer_search": False,
    }
    
    result = interpret_query("Найди Fender до 1000$", llm_client=mock_llm)
    
    assert result["mode"] == "search"
    assert "results" in result
    assert len(result["results"]) > 0
    
    first_result = result["results"][0]
    assert "id" in first_result
    assert "title" in first_result
    assert "price" in first_result
    assert "currency" in first_result
    assert "listing_url" in first_result

def test_full_flow_consultation(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    
    mock_llm = MagicMock()
    mock_llm.classify_and_plan_query.return_value = {
        "intent": "consultation",
        "enough_for_search": False,
        "missing_fields": [],
        "search_params": None,
        "should_offer_search": False,
    }
    mock_llm.ask.return_value = "Stratocaster и Telecaster - это две классические модели..."
    
    result = interpret_query("Чем отличается Stratocaster от Telecaster?", llm_client=mock_llm)
    
    assert result["mode"] == "consultation"
    assert "answer" in result
    assert len(result["answer"]) > 0

def test_full_flow_no_api_key_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    from backend.agent.service import LLMUnavailableError

    with pytest.raises(LLMUnavailableError):
        interpret_query("Найди Gibson", llm_client=None)
