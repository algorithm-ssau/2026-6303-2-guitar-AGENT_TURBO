"""Интеграционные проверки agent service вокруг LLM-router."""

from unittest.mock import MagicMock

import pytest

from backend.agent.clarification import CLARIFICATION_QUESTIONS
from backend.agent.service import InvalidRouterResponseError, interpret_query


def route(intent="search", search_params=None, enough=True, missing=None, offer=False):
    return {
        "intent": intent,
        "enough_for_search": enough,
        "missing_fields": missing or [],
        "search_params": search_params if intent == "search" else None,
        "should_offer_search": offer,
    }


def test_search_returns_results_and_search_params():
    client = MagicMock()
    client.classify_and_plan_query.return_value = route(search_params={
        "search_queries": ["PRS SE Custom 24"],
        "price_max": 900,
        "type": "superstrat",
        "brand": "PRS",
    })

    result = interpret_query(
        "Подбери PRS до 900",
        llm_client=client,
        search_fn=lambda *args: [{"title": "PRS SE Custom 24", "price": 850}],
    )

    assert result["mode"] == "search"
    assert result["search_params"]["brand"] == "PRS"


def test_clarification_uses_router_missing_fields():
    client = MagicMock()
    client.classify_and_plan_query.return_value = route(
        search_params={"search_queries": [], "type": None, "price_max": None},
        enough=False,
        missing=["budget", "type"],
    )
    client.ask.return_value = "Напишите бюджет, а тип можно не выбирать: подберу вариант для новичка."

    result = interpret_query("Подбери гитару", llm_client=client)

    assert result["mode"] == "clarification"
    assert "бюджет" in result["question"].lower()
    assert result["question"] == "Напишите бюджет, а тип можно не выбирать: подберу вариант для новичка."
    assert result["question"] != CLARIFICATION_QUESTIONS["both"]


def test_incomplete_search_route_with_null_search_params_returns_clarification():
    client = MagicMock()
    client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": False,
        "missing_fields": ["budget", "type"],
        "search_params": None,
        "should_offer_search": False,
    }
    client.ask.return_value = "Скажите бюджет; если с типом не уверены, так и напишите."

    result = interpret_query("хорошую гитарку для новичка посоветуй давай", llm_client=client)

    assert result["mode"] == "clarification"
    assert "бюджет" in result["question"].lower()
    assert result["question"] != CLARIFICATION_QUESTIONS["both"]


def test_consultation_answer_is_generated_separately():
    client = MagicMock()
    client.classify_and_plan_query.return_value = route(intent="consultation", enough=False, offer=False)
    client.ask.return_value = "Single-coil ярче, humbucker плотнее."

    result = interpret_query("Чем отличаются сингл и хамбакер?", llm_client=client)

    assert result["mode"] == "consultation"
    assert result["answer"] == "Single-coil ярче, humbucker плотнее."


def test_router_must_return_search_params_for_search():
    client = MagicMock()
    client.classify_and_plan_query.return_value = route(search_params=None)

    with pytest.raises(InvalidRouterResponseError):
        interpret_query("Подбери гитару", llm_client=client)


def test_type_no_preference_runs_search_without_type_clarification():
    client = MagicMock()
    client.classify_and_plan_query.return_value = route(search_params={
        "search_queries": ["beginner electric guitar"],
        "price_max": 500,
        "type": "any",
    })
    client.classify_and_plan_query.return_value["no_preference_fields"] = ["type"]

    result = interpret_query(
        "500 долларов, а тип я не знаю",
        llm_client=client,
        search_fn=lambda queries, price_min, price_max: [{"title": "Starter Guitar", "price": 450}],
    )

    assert result["mode"] == "search"
    assert result["search_params"]["type"] == "any"
    assert result["search_params"]["price_max"] == 500


def test_budget_unknown_returns_dynamic_default_confirmation(monkeypatch):
    saved_states = []
    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: {"asked_fields": ["budget"]})
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: saved_states.append(state))

    client = MagicMock()
    client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": False,
        "missing_fields": ["budget"],
        "no_preference_fields": ["type"],
        "budget_default_offer": True,
        "default_actions": [],
        "search_params": {"type": "any", "search_queries": []},
        "should_offer_search": False,
    }
    client.ask.return_value = "Ок, показать недорогие варианты для новичка до $500?"

    result = interpret_query("бюджет не знаю", llm_client=client, session_id=42)

    assert result["mode"] == "clarification"
    assert result["question"] == "Ок, показать недорогие варианты для новичка до $500?"
    assert saved_states[-1]["pending_defaults"]["budget"]["price_max"] == 500


def test_pending_budget_default_confirmation_applies_default(monkeypatch):
    monkeypatch.setattr(
        "backend.agent.service.get_session_state",
        lambda session_id: {
            "pending_defaults": {"budget": {"kind": "beginner_cheap", "price_max": 500}},
            "type": "any",
            "missing_fields": ["budget"],
            "price_max": 1000,
        },
    )
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)

    client = MagicMock()
    client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "no_preference_fields": ["type"],
        "default_actions": ["accept_beginner_budget"],
        "search_params": {
            "search_queries": ["beginner electric guitar"],
            "price_min": None,
            "price_max": None,
            "type": "any",
        },
        "should_offer_search": False,
    }

    result = interpret_query(
        "да",
        llm_client=client,
        search_fn=lambda queries, price_min, price_max: [{"title": "Starter Guitar", "price": 450}],
        session_id=42,
    )

    assert result["mode"] == "search"
    assert result["search_params"]["price_max"] == 500


def test_no_extra_questions_beginner_request_applies_default_without_confirmation():
    client = MagicMock()
    client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "no_preference_fields": ["type"],
        "default_actions": ["apply_beginner_budget"],
        "search_params": {
            "search_queries": ["beginner electric guitar"],
            "price_min": None,
            "price_max": None,
            "type": "any",
        },
        "should_offer_search": False,
    }

    result = interpret_query(
        "хочу гитару, я новичок, ничего не понимаю, без лишних вопросов",
        llm_client=client,
        search_fn=lambda queries, price_min, price_max: [{"title": "Starter Guitar", "price": 450}],
    )

    assert result["mode"] == "search"
    assert result["search_params"]["price_max"] == 500


def test_budget_no_preference_without_default_does_not_allow_unlimited_ready_search():
    client = MagicMock()
    client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "no_preference_fields": ["budget"],
        "default_actions": [],
        "search_params": {
            "search_queries": ["beginner electric guitar"],
            "price_min": None,
            "price_max": None,
            "type": "any",
        },
        "should_offer_search": False,
    }

    with pytest.raises(InvalidRouterResponseError):
        interpret_query("бюджет не знаю", llm_client=client)


def test_state_action_reset_drops_stale_search_state(monkeypatch):
    monkeypatch.setattr(
        "backend.agent.service.get_session_state",
        lambda session_id: {"type": "telecaster", "price_max": 1000, "search_queries": ["Fender Telecaster"]},
    )
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)

    client = MagicMock()
    client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "state_action": "reset",
        "search_params": {
            "search_queries": ["beginner electric guitar"],
            "price_min": None,
            "price_max": 500,
            "type": "any",
        },
        "should_offer_search": False,
    }

    result = interpret_query(
        "хочу гитару для новичка",
        llm_client=client,
        search_fn=lambda queries, price_min, price_max: [{"title": "Starter Guitar", "price": 450}],
        session_id=42,
    )

    assert result["mode"] == "search"
    assert result["search_params"]["type"] == "any"
    assert result["search_params"]["price_max"] == 500
    assert result["search_params"]["search_queries"] == ["beginner electric guitar"]


def test_explicit_budget_patch_overrides_stale_beginner_default_clarification(monkeypatch):
    saved_states = []
    monkeypatch.setattr(
        "backend.agent.service.get_session_state",
        lambda session_id: {
            "type": "any",
            "price_max": 500,
            "search_queries": ["beginner electric guitar"],
            "ready_for_search": True,
            "default_actions": ["apply_beginner_budget"],
        },
    )
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: saved_states.append(state))

    client = MagicMock()
    client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": False,
        "missing_fields": ["budget"],
        "no_preference_fields": ["type"],
        "budget_default_offer": True,
        "default_actions": [],
        "state_action": "patch",
        "search_params": {
            "search_queries": [],
            "price_min": None,
            "price_max": 1000,
            "type": "any",
        },
        "should_offer_search": False,
    }

    result = interpret_query(
        "давай до 1000 доларов",
        llm_client=client,
        search_fn=lambda queries, price_min, price_max: [{"title": "Starter Guitar", "price": 650}],
        session_id=42,
    )

    assert result["mode"] == "search"
    assert result["search_params"]["price_max"] == 1000
    assert result["search_params"]["search_queries"] == ["beginner electric guitar"]
    assert not saved_states[-1].get("pending_defaults", {}).get("budget")


def test_explicit_type_patch_removes_contradictory_type_missing_field(monkeypatch):
    monkeypatch.setattr(
        "backend.agent.service.get_session_state",
        lambda session_id: {
            "type": "any",
            "price_max": 500,
            "search_queries": ["beginner electric guitar"],
            "ready_for_search": True,
        },
    )
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)

    client = MagicMock()
    client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": False,
        "missing_fields": ["type"],
        "no_preference_fields": [],
        "budget_default_offer": False,
        "default_actions": [],
        "state_action": "patch",
        "search_params": {
            "search_queries": ["Squier Telecaster"],
            "price_min": None,
            "price_max": None,
            "type": "telecaster",
        },
        "should_offer_search": False,
    }

    result = interpret_query(
        "давай телекастер",
        llm_client=client,
        search_fn=lambda queries, price_min, price_max: [{"title": "Squier Telecaster", "price": 450}],
        session_id=42,
    )

    assert result["mode"] == "search"
    assert result["search_params"]["type"] == "telecaster"
