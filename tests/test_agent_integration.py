"""Тесты логики интерпретации запроса (service.py) с использованием мока Groq-клиента."""

import pytest
from unittest.mock import MagicMock
from backend.agent.service import interpret_query

def test_interpret_query_search_mode():
    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {
            "search_queries": ["Jackson JS22"],
            "price_max": 450,
            "type": "Superstrat",
        },
        "consultation_answer": "",
        "should_offer_search": False,
    }
    mock_client.extract_search_params.return_value = {
        "search_queries": ["Jackson JS22"],
        "price_max": 450,
        "type": "Superstrat",
    }

    result = interpret_query("Нужна гитара для металла до 45к", llm_client=mock_client)
    assert result["mode"] == "search"
    assert "results" in result
    assert isinstance(result["results"], list)

def test_interpret_query_consultation_mode():
    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "consultation",
        "enough_for_search": False,
        "missing_fields": [],
        "search_params": None,
        "consultation_answer": "Синглы звучат ярче.",
        "should_offer_search": False,
    }

    result = interpret_query("Чем отличаются синглы?", llm_client=mock_client)
    assert result["mode"] == "consultation"
    assert result["answer"] == "Синглы звучат ярче."

def test_interpret_query_invalid_json():
    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = "bad"
    mock_client.ask.side_effect = Exception("API Error")

    result = interpret_query("Привет", llm_client=mock_client)
    assert result["mode"] == "consultation"
    assert "Извините, произошла ошибка" in result["answer"]


def test_interpret_query_uses_history_after_clarification(monkeypatch):
    session_history = [
        {
            "user_query": "Ищу Stratocaster до 1200$",
            "mode": "consultation",
            "answer": "Норм, могу подобрать.",
            "results": None,
        },
        {
            "user_query": "подбери теперь варианты и ссылки на них",
            "mode": "clarification",
            "answer": "Уточните, пожалуйста, какой у вас бюджет и какой тип гитары вы ищете?",
            "results": None,
        },
    ]

    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: session_history)
    monkeypatch.setattr("backend.agent.context_manager.get_session_messages", lambda session_id: session_history)
    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: {})
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {
            "search_queries": ["Fender Stratocaster"],
            "price_max": 1200,
            "type": "Stratocaster",
        },
        "consultation_answer": "",
        "should_offer_search": False,
    }
    mock_client.extract_search_params.return_value = {
        "search_queries": ["Fender Stratocaster"],
        "price_max": 1200,
        "type": "Stratocaster",
    }

    search_results = [{
        "id": "1",
        "title": "Fender Player Stratocaster",
        "price": 999,
        "currency": "USD",
        "listing_url": "https://example.com/strat",
    }]

    result = interpret_query(
        "я же писал выше",
        llm_client=mock_client,
        search_fn=lambda *args: search_results,
        session_id=1,
    )

    assert result["mode"] == "search"
    assert result["results"]
    assert mock_client.classify_and_plan_query.call_args.args[0] == "я же писал выше"
    assert mock_client.classify_and_plan_query.call_args.kwargs["history"]


def test_stateful_follow_up_uses_saved_budget_and_type(monkeypatch):
    session_history = []
    stored_state = {"type": "Telecaster", "price_max": 600, "ready_for_search": True, "missing_fields": []}
    saved_states = []

    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: session_history)
    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: stored_state)
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: saved_states.append(state))

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {"search_queries": ["Telecaster"]},
        "consultation_answer": "",
        "should_offer_search": False,
    }

    result = interpret_query(
        "покажи уже варианты ссылки",
        llm_client=mock_client,
        search_fn=lambda queries, *_: [{"id": "1", "title": queries[0], "price": 399}],
        session_id=19,
    )

    assert result["mode"] == "search"
    assert result["results"][0]["title"] == "Telecaster"
    assert saved_states[-1]["price_max"] == 600


def test_zero_results_relaxes_query_to_type():
    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {
            "search_queries": ["Fender Player Telecaster"],
            "price_max": 600,
            "type": "Telecaster",
            "brand": "Fender",
        },
        "consultation_answer": "",
        "should_offer_search": False,
    }

    calls = []

    def fake_search(queries, price_min, price_max):
        calls.append(list(queries))
        if queries == ["Fender Player Telecaster"]:
            return []
        return [{"id": "1", "title": "Squier Affinity Telecaster", "price": 249}]

    result = interpret_query(
        "Хочу телекастер с ярким звуком, до $600",
        llm_client=mock_client,
        search_fn=fake_search,
    )

    assert result["mode"] == "search"
    assert result["results"]
    assert calls[0] == ["Fender Player Telecaster"]
    assert "Telecaster" in calls[1]


def test_any_type_reply_stops_type_clarification_loop(monkeypatch):
    stored_state = {
        "price_max": 600,
        "search_queries": ["guitar"],
        "missing_fields": ["type"],
        "ready_for_search": False,
        "last_clarification_target": "type",
    }
    saved_states = []

    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: stored_state)
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: saved_states.append(state))
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: [])

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {
            "search_queries": ["guitar"],
            "price_max": 600,
            "type": "any",
            "sound": "bright",
        },
        "consultation_answer": "",
        "should_offer_search": False,
    }

    result = interpret_query(
        "да мне пофиг",
        llm_client=mock_client,
        search_fn=lambda queries, *_: [{"id": "1", "title": queries[0], "price": 499}],
        session_id=21,
    )

    assert result["mode"] == "search"
    assert result["results"]
    assert saved_states[-1]["type"] == "any"


def test_no_preference_reply_can_clear_budget_requirement(monkeypatch):
    stored_state = {
        "type": "Telecaster",
        "missing_fields": ["budget"],
        "ready_for_search": False,
        "last_clarification_target": "budget",
    }
    saved_states = []

    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: stored_state)
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: saved_states.append(state))
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: [])

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": False,
        "missing_fields": ["budget"],
        "search_params": {"search_queries": ["Telecaster"], "type": "Telecaster"},
        "consultation_answer": "",
        "should_offer_search": False,
    }

    result = interpret_query(
        "мне по барабану",
        llm_client=mock_client,
        search_fn=lambda queries, *_: [{"id": "1", "title": queries[0], "price": 799}],
        session_id=21,
    )

    assert result["mode"] == "search"
    assert result["results"]
    assert "budget" in saved_states[-1]["no_preference_fields"]


def test_pofig_reply_resolves_type_clarification_from_history_state(monkeypatch):
    stored_state = {
        "price_max": 600,
        "sound": "bright",
        "missing_fields": ["type"],
        "ready_for_search": False,
        "last_clarification_target": "type",
    }
    saved_states = []

    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: stored_state)
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: saved_states.append(state))
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: [])

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {
            "search_queries": ["guitar"],
            "price_max": 600,
            "type": "any",
            "sound": "bright",
        },
        "consultation_answer": "",
        "should_offer_search": False,
    }

    result = interpret_query(
        "да мне пофиг",
        llm_client=mock_client,
        search_fn=lambda queries, *_: [{"id": "1", "title": queries[0], "price": 450}],
        session_id=22,
    )

    assert result["mode"] == "search"
    assert saved_states[-1]["last_clarification_target"] is None


def test_price_only_request_runs_search_without_clarification():
    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {
            "search_queries": [],
            "price_max": 600,
        },
        "consultation_answer": "",
        "should_offer_search": False,
    }

    calls = []

    def fake_search(queries, price_min, price_max):
        calls.append((list(queries), price_min, price_max))
        return [{"id": "1", "title": "Any Guitar", "price": 450}]

    result = interpret_query(
        "до 600 долларов",
        llm_client=mock_client,
        search_fn=fake_search,
    )

    assert result["mode"] == "search"
    assert result["results"]
    assert calls[0][0] == ["guitar"]
    assert calls[0][2] == 600


def test_any_type_reply_uses_broad_query_instead_of_sound(monkeypatch):
    stored_state = {
        "price_max": 600,
        "sound": "bright",
        "missing_fields": ["type"],
        "ready_for_search": False,
        "last_clarification_target": "type",
    }

    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: stored_state)
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: [])

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {
            "search_queries": [],
            "price_max": 600,
            "type": "any",
            "sound": "bright",
        },
        "consultation_answer": "",
        "should_offer_search": False,
    }

    calls = []

    def fake_search(queries, price_min, price_max):
        calls.append(list(queries))
        return [{"id": "1", "title": "Any Guitar", "price": 450}]

    result = interpret_query(
        "да мне пофиг",
        llm_client=mock_client,
        search_fn=fake_search,
        session_id=22,
    )

    assert result["mode"] == "search"
    assert calls[0] == ["guitar"]


def test_followup_no_results_phrase_resumes_search(monkeypatch):
    stored_state = {
        "price_max": 600,
        "sound": "bright",
        "type": "any",
        "search_queries": ["guitar"],
        "missing_fields": [],
        "ready_for_search": True,
        "last_intent": "search",
    }

    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: stored_state)
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: [])

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "consultation",
        "enough_for_search": False,
        "missing_fields": [],
        "search_params": None,
        "consultation_answer": "Это выглядит как консультация.",
        "should_offer_search": False,
    }

    result = interpret_query(
        "тоесть у тебя нет гитар с ярким звуком до 600?",
        llm_client=mock_client,
        search_fn=lambda queries, *_: [{"id": "1", "title": queries[0], "price": 500}],
        session_id=22,
    )

    assert result["mode"] == "search"
    assert result["results"][0]["title"] == "guitar"


def test_consultation_question_is_not_hijacked_by_previous_search(monkeypatch):
    stored_state = {
        "price_max": 600,
        "type": "Telecaster",
        "search_queries": ["Telecaster"],
        "missing_fields": [],
        "ready_for_search": True,
        "last_intent": "search",
    }

    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: stored_state)
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: [])

    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "consultation",
        "enough_for_search": False,
        "missing_fields": [],
        "search_params": None,
        "consultation_answer": "Single-coil обычно ярче humbucker.",
        "should_offer_search": False,
    }

    result = interpret_query(
        "а ты не знаешь, чем single-coil отличается от humbucker?",
        llm_client=mock_client,
        search_fn=lambda *args: [{"id": "1", "title": "Telecaster", "price": 500}],
        session_id=22,
    )

    assert result["mode"] == "consultation"
    assert "single-coil" in result["answer"].lower()


def test_interpret_query_sanitizes_catalog_like_consultation_answer():
    mock_client = MagicMock()
    mock_client.extract_search_params.return_value = {
        "search_queries": ["Fender Telecaster"],
        "price_max": 1200,
        "type": "Telecaster",
    }

    result = interpret_query(
        "покажи ссылки на телекастеры",
        llm_client=mock_client,
        search_fn=lambda *args: [{"id": "1", "title": "Fender Telecaster", "price": 999}],
    )

    assert result["mode"] == "search"


def test_handle_consultation_blocks_catalog_like_answer():
    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "consultation",
        "enough_for_search": False,
        "missing_fields": [],
        "search_params": None,
        "consultation_answer": "Fender American Professional Telecaster, Fender Player Telecaster, Reverb.com",
        "should_offer_search": True,
    }

    result = interpret_query("в чем разница между синглом и хамбакером", llm_client=mock_client)

    assert result["mode"] == "consultation"
    assert "только реальные варианты из каталога" in result["answer"]


def test_stratocaster_with_budget_and_links_does_not_trigger_clarification():
    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {
            "search_queries": ["Stratocaster"],
            "price_max": 1200,
        },
        "consultation_answer": "",
        "should_offer_search": False,
    }
    mock_client.extract_search_params.return_value = {
        "search_queries": ["Stratocaster"],
        "price_max": 1200,
    }

    result = interpret_query(
        "Подбери Stratocaster до 1200$ и дай ссылки",
        llm_client=mock_client,
        search_fn=lambda *args: [{"id": "1", "title": "Fender Stratocaster", "price": 999}],
    )

    assert result["mode"] == "search"
    assert result["results"]


def test_consultation_falls_back_to_legacy_ask_signature():
    class LegacyLLM:
        def classify_and_plan_query(self, text: str, history=None) -> dict:
            return {
                "intent": "consultation",
                "enough_for_search": False,
                "missing_fields": [],
                "search_params": None,
                "consultation_answer": "",
                "should_offer_search": False,
            }

        def ask(self, text: str, system_prompt: str) -> str:
            return "Сингл ярче, хамбакер плотнее."

    result = interpret_query("что такое хамбакер", llm_client=LegacyLLM(), session_id=None)

    assert result["mode"] == "consultation"
    assert "хамбакер" in result["answer"].lower()


def test_router_search_with_enough_data_goes_directly_to_search():
    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {
            "search_queries": ["Fender Telecaster", "Squier Telecaster"],
            "price_max": 600,
            "type": "Telecaster",
            "sound": "bright",
        },
        "consultation_answer": "",
        "should_offer_search": False,
    }

    result = interpret_query(
        "Хочу телекастер с ярким звуком, до $600",
        llm_client=mock_client,
        search_fn=lambda *args: [{"id": "1", "title": "Squier Telecaster", "price": 399}],
    )

    assert result["mode"] == "search"
    assert result["results"]


def test_router_missing_fields_do_not_block_search_when_type_is_known():
    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "search",
        "enough_for_search": False,
        "missing_fields": ["budget"],
        "search_params": {
            "search_queries": ["Telecaster"],
            "type": "Telecaster",
            "price_max": None,
        },
        "consultation_answer": "",
        "should_offer_search": False,
    }

    result = interpret_query("Хочу телекастер", llm_client=mock_client)

    assert result["mode"] == "search"
    assert isinstance(result["results"], list)


def test_consultation_offer_text_is_appended_without_external_links():
    mock_client = MagicMock()
    mock_client.classify_and_plan_query.return_value = {
        "intent": "consultation",
        "enough_for_search": False,
        "missing_fields": [],
        "search_params": None,
        "consultation_answer": "Для яркого звука у Telecaster обычно хорошо работают single-coil и жёсткая атака.",
        "should_offer_search": True,
    }

    result = interpret_query("Почему Telecaster звучит ярко?", llm_client=mock_client)

    assert result["mode"] == "consultation"
    assert "reverb" in result["answer"].lower()
    assert "amazon" not in result["answer"].lower()
