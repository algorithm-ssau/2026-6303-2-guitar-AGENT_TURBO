import os
import pytest
from unittest.mock import MagicMock
from backend.agent.llm_client import LLMClient

def test_llm_client_missing_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        LLMClient()

def test_llm_client_ask_success(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    client = LLMClient()
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Тестовый ответ"
    client.client.chat.completions.create = MagicMock(return_value=mock_response)
    
    result = client.ask("Привет", "Ты агент")
    assert result == "Тестовый ответ"

def test_extract_search_params_success(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    client = LLMClient()
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"search_queries": ["Fender"], "price_max": 1000}'
    client.client.chat.completions.create = MagicMock(return_value=mock_response)
    
    result = client.extract_search_params("Хочу Fender до 1000")
    assert result["search_queries"] == ["Fender"]
    assert result["price_max"] == 1000

def test_extract_search_params_invalid_json(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    client = LLMClient()
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Не JSON, просто текст"
    client.client.chat.completions.create = MagicMock(return_value=mock_response)
    
    result = client.extract_search_params("Привет")
    assert result["search_queries"] == []
    assert result["price_min"] is None
    assert result["price_max"] is None
