import os
import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
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


def test_classify_and_plan_query_success(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    client = LLMClient()

    mock_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content='{"intent": "search", "enough_for_search": true, "missing_fields": [], "search_params": {"search_queries": ["Fender Telecaster"], "price_max": 600, "type": "Telecaster"}, "consultation_answer": "", "should_offer_search": false}'
                )
            )
        ]
    )
    client.client.chat.completions.create = MagicMock(return_value=mock_response)

    result = client.classify_and_plan_query("Хочу телекастер до 600$")
    assert result["intent"] == "search"
    assert result["search_params"]["type"] == "Telecaster"


def test_extract_search_params_includes_history_context(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    client = LLMClient()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"search_queries": ["Fender Stratocaster"], "price_max": 1200}'
    client.client.chat.completions.create = MagicMock(return_value=mock_response)

    history = [
        {"role": "user", "content": "Ищу Stratocaster до 1200$"},
        {"role": "assistant", "content": "Могу подобрать варианты со ссылками."},
    ]

    client.extract_search_params("подбери теперь варианты и ссылки на них", history=history)

    prompt = client.client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "Контекст предыдущего диалога" in prompt
    assert "Ищу Stratocaster до 1200$" in prompt
