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
    mock_llm.extract_search_params.return_value = {"search_queries": ["Fender"], "price_max": 1000}
    
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
    mock_llm.ask.return_value = "Stratocaster и Telecaster - это две классические модели..."
    
    result = interpret_query("Чем отличается Stratocaster от Telecaster?", llm_client=mock_llm)
    
    assert result["mode"] == "consultation"
    assert "answer" in result
    assert len(result["answer"]) > 0

def test_full_flow_fallback_no_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    
    # Passing llm_client=None explicitly forces interpret_query to call create_llm_client() which returns None
    result = interpret_query("Найди Gibson", llm_client=None)
    
    # Since the word "Найди" is used, detect_mode should determine it's a "search"
    assert result["mode"] == "search"
    assert "results" in result
    # It will fall back to using the raw query as search_queries and still run the mock search
    assert isinstance(result["results"], list)
