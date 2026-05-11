import os
import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from backend.agent.llm_client import (
    LLMClient,
    build_router_prompt_for_debug,
    build_router_repair_prompt_for_debug,
)

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

def test_classify_and_plan_query_success(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    monkeypatch.setenv("LLM_ROUTER_MODEL", "router-test-model")
    client = LLMClient()

    mock_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content='{"intent": "search", "enough_for_search": true, "missing_fields": [], "search_params": {"search_queries": ["Fender Telecaster"], "price_max": 600, "type": "telecaster"}, "should_offer_search": false}'
                )
            )
        ]
    )
    client.client.chat.completions.create = MagicMock(return_value=mock_response)

    result = client.classify_and_plan_query("Хочу телекастер до 600$")
    assert result["intent"] == "search"
    assert result["search_params"]["type"] == "telecaster"
    assert client.client.chat.completions.create.call_args.kwargs["model"] == "router-test-model"


def test_classify_and_plan_query_includes_history_context(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    client = LLMClient()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        '{"intent":"search","enough_for_search":true,"missing_fields":[],'
        '"search_params":{"search_queries":["Fender Stratocaster"],"price_max":1200},'
        '"should_offer_search":false}'
    )
    client.client.chat.completions.create = MagicMock(return_value=mock_response)

    history = [
        {"role": "user", "content": "Ищу Stratocaster до 1200$"},
        {"role": "assistant", "content": "Могу подобрать варианты со ссылками."},
    ]

    client.classify_and_plan_query("подбери теперь варианты и ссылки на них", history=history)

    prompt = client.client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "Контекст:" in prompt
    assert "Ищу Stratocaster до 1200$" in prompt


def test_llm_client_uses_split_router_and_answer_models(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    monkeypatch.setenv("LLM_MODEL", "base-answer-model")
    monkeypatch.setenv("LLM_ROUTER_MODEL", "router-model")
    monkeypatch.setenv("LLM_ANSWER_MODEL", "answer-model")
    client = LLMClient()

    answer_response = MagicMock()
    answer_response.choices[0].message.content = "Ответ"
    router_response = MagicMock()
    router_response.choices[0].message.content = (
        '{"intent":"consultation","enough_for_search":false,"missing_fields":[],'
        '"search_params":null,"should_offer_search":true}'
    )
    client.client.chat.completions.create = MagicMock(side_effect=[answer_response, router_response])

    assert client.ask("Что такое хамбакер?", "Ты консультант") == "Ответ"
    client.classify_and_plan_query("Что такое хамбакер?")

    assert client.client.chat.completions.create.call_args_list[0].kwargs["model"] == "answer-model"
    assert client.client.chat.completions.create.call_args_list[1].kwargs["model"] == "router-model"


def test_router_repair_prompt_contains_validation_errors_and_invalid_json():
    prompt = build_router_repair_prompt_for_debug(
        "Хочу телекастер с ярким звуком, до $600",
        invalid_plan={
            "intent": "search",
            "enough_for_search": True,
            "missing_fields": [],
            "search_params": {"search_queries": []},
        },
        validation_errors=[
            "search_params.search_queries must contain at least one non-empty query when enough_for_search=true"
        ],
        history=[{"role": "assistant", "content": "Последняя поисковая выдача:\n#1 Fender Telecaster, $599"}],
        current_state={"price_max": 600},
    )

    assert "Ошибки" not in prompt
    assert "Validation errors:" in prompt
    assert "search_queries" in prompt
    assert "Хочу телекастер" in prompt
    assert "Последняя поисковая выдача" in prompt


def test_repair_router_plan_uses_router_model(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    monkeypatch.setenv("LLM_ROUTER_MODEL", "router-repair-model")
    client = LLMClient()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        '{"intent":"search","enough_for_search":true,"missing_fields":[],'
        '"search_params":{"search_queries":["Fender Telecaster"],"price_max":600},'
        '"should_offer_search":false}'
    )
    client.client.chat.completions.create = MagicMock(return_value=mock_response)

    result = client.repair_router_plan(
        "Хочу телекастер до 600",
        invalid_plan={"intent": "search", "search_params": {"search_queries": []}},
        validation_errors=["search_params.search_queries must contain at least one non-empty query when enough_for_search=true"],
    )

    assert result["search_params"]["search_queries"] == ["Fender Telecaster"]
    assert client.client.chat.completions.create.call_args.kwargs["model"] == "router-repair-model"


def test_clarify_search_uses_answer_model(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    monkeypatch.setenv("LLM_ANSWER_MODEL", "answer-clarification-model")
    client = LLMClient()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Ок, показать недорогие варианты для новичка до $500?"
    client.client.chat.completions.create = MagicMock(return_value=mock_response)

    result = client.clarify_search(
        "бюджет не знаю",
        "clarification prompt",
        payload={"missing_fields": ["budget"], "budget_default_offer": True},
    )

    assert result == "Ок, показать недорогие варианты для новичка до $500?"
    assert client.client.chat.completions.create.call_args.kwargs["model"] == "answer-clarification-model"


def test_router_json_parse_failure_returns_empty_candidate(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    client = LLMClient()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "not json"
    client.client.chat.completions.create = MagicMock(return_value=mock_response)

    assert client.classify_and_plan_query("Подбери гитару") == {}
    assert client.repair_router_plan("Подбери гитару", {}, ["intent must be one of search, consultation, off_topic"]) == {}


def test_router_prompt_size_stays_under_budget_for_beginner_recommendation():
    prompt = build_router_prompt_for_debug("хорошую гитарку для новичка посоветуй давай")

    assert len(prompt) < 3300


def test_router_prompt_size_with_no_preference_rules_stays_under_budget():
    prompt = build_router_prompt_for_debug("хочу гитару, я новичок, ничего не понимаю, без лишних вопросов")

    assert len(prompt) < 3600


def test_router_prompt_size_with_short_history_and_state_stays_under_budget():
    history = [
        {
            "role": "assistant",
            "content": (
                "Последняя поисковая выдача:\n"
                "#1 Fender Player Telecaster, $799\n"
                "#2 Squier Classic Vibe Telecaster, $429"
            ),
        },
        {"role": "user", "content": "давай до 1000 баксов"},
    ]
    state = {
        "price_max": 1000,
        "type": "telecaster",
        "search_queries": ["Fender Telecaster"],
        "ready_for_search": True,
    }

    prompt = build_router_prompt_for_debug(
        "для начала как новичку что лучше взять?",
        history=history,
        current_state=state,
    )

    assert len(prompt) < 4000
