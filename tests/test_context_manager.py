import pytest
from unittest.mock import MagicMock, patch
from backend.agent.context_manager import estimate_tokens, build_context

def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("абв") == 1
    assert estimate_tokens("это тест на токены") == 6

@patch("backend.agent.context_manager.get_session_messages")
def test_build_context_short(mock_get_messages):
    mock_get_messages.return_value = [
        {"user_query": "привет", "answer": "здравствуйте", "mode": "consultation"}
    ]
    mock_llm = MagicMock()
    
    history = build_context(1, "system", "text", mock_llm)
    
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    mock_llm.summarize.assert_not_called()

@patch("backend.agent.context_manager.get_session_messages")
@patch("os.getenv")
def test_build_context_long_with_summary(mock_getenv, mock_get_messages):
    mock_getenv.return_value = "10" 
    
    mock_get_messages.return_value = [
        {"user_query": f"сообщение {i}", "answer": f"ответ {i}", "mode": "consultation"}
        for i in range(10)
    ]
    
    mock_llm = MagicMock()
    mock_llm.summarize.return_value = "Суммаризация"
    
    history = build_context(1, "system", "txt", mock_llm)
    
    mock_llm.summarize.assert_called_once()
    
    assert len(history) == 7
    assert history[0]["role"] == "system"
    assert history[0]["content"] == "Суммаризация"

@patch("backend.agent.context_manager.get_session_messages")
@patch("os.getenv")
def test_build_context_fallback_no_llm(mock_getenv, mock_get_messages):
    mock_getenv.return_value = "10" 
    
    mock_get_messages.return_value = [
        {"user_query": f"msg", "answer": f"ans", "mode": "consultation"}
        for i in range(10)
    ]
    
    history = build_context(1, "sys", "txt", None)
    
    assert len(history) == 10

def test_build_context_no_session():
    history = build_context(None, "sys", "txt", None)
    assert history == []
