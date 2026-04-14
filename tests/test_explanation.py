import pytest
import os
from unittest.mock import MagicMock
from backend.agent.explanation import generate_explanation

def test_generate_explanation_with_llm():
    mock_llm = MagicMock()
    mock_llm.ask.return_value = "Это отличные гитары для металла."
    
    results = [{"title": "Ibanez"}, {"title": "Jackson"}]
    explanation = generate_explanation("металл 500$", results, mock_llm)
    
    assert explanation == "Это отличные гитары для металла."
    mock_llm.ask.assert_called_once()
    args, kwargs = mock_llm.ask.call_args
    assert "Ibanez" in args[0]
    assert "Jackson" in args[0]
    
def test_generate_explanation_without_llm():
    results = [{"title": "Ibanez"}]
    explanation = generate_explanation("металл", results, None)
    assert explanation == ""
    
def test_generate_explanation_empty_results():
    mock_llm = MagicMock()
    explanation = generate_explanation("металл", [], mock_llm)
    assert explanation == ""

def test_generate_explanation_llm_error():
    mock_llm = MagicMock()
    mock_llm.ask.side_effect = Exception("LLM Error")
    
    results = [{"title": "Ibanez"}]
    explanation = generate_explanation("металл", results, mock_llm)
    assert explanation == ""
