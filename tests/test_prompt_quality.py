import pytest
import os
from backend.agent.param_extractor import build_search_prompt

def test_prompt_quality_few_shot():
    prompt = build_search_prompt("test", "mapping")
    assert "50к деревянных" in prompt, "Missing russian slang few-shot example"
    assert "жирную гитару" in prompt, "Missing sound characteristics few-shot example"

def test_prompt_quality_agent_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "../docs/AGENT_PROMPT.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "100 руб/доллар" in content, "Missing ruble conversion rule"
    assert "конкретную модель" in content, "Missing specific model rule"

def test_prompt_quality_consultation_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "../docs/CONSULTATION_PROMPT.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "до 300 слов" in content, "Missing words limit limit"
    assert "форматированный текст" in content or "структурированный текст" in content, "Missing format rule"
