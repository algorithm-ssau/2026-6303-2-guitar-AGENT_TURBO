"""Сценарные тесты агента по актуальному LLM-router contract."""

from unittest.mock import MagicMock

from backend.agent.service import (
    _build_router_history,
    _looks_like_catalog_content,
    interpret_query,
)


def make_client(route_plan, answer="Синглы звучат ярче, а хамбакеры плотнее."):
    client = MagicMock()
    client.classify_and_plan_query.return_value = route_plan
    client.ask.return_value = answer
    return client


def search_route(search_params, enough=True, missing=None):
    return {
        "intent": "search",
        "enough_for_search": enough,
        "missing_fields": missing or [],
        "search_params": search_params,
        "should_offer_search": False,
    }


def consultation_route(offer=False):
    return {
        "intent": "consultation",
        "enough_for_search": False,
        "missing_fields": [],
        "search_params": None,
        "should_offer_search": offer,
    }


def mock_search(*args):
    return [{"title": "Fender Player Stratocaster", "price": 900}]


def test_scenario_1_direct_search():
    client = make_client(search_route({
        "search_queries": ["Fender Player Stratocaster", "Squier Classic Vibe Telecaster"],
        "price_max": 1000,
        "type": "stratocaster",
    }))

    result = interpret_query(
        "Привет! Ищу яркую электрогитару для блюза и фанка, бюджет до 1000 баксов.",
        llm_client=client,
        search_fn=mock_search,
    )

    assert result["mode"] == "search"
    assert result["search_params"]["price_max"] == 1000
    assert result["search_params"]["search_queries"]


def test_scenario_2_lack_of_data():
    client = make_client(search_route(
        {"search_queries": ["metal guitar"], "style": "metal"},
        enough=False,
        missing=["budget"],
    ), answer="Какой бюджет держим для гитары под металл?")

    result = interpret_query("Хочу купить гитару для метала.", llm_client=client)

    assert result["mode"] == "clarification"
    assert "бюджет" in result["question"]


def test_scenario_3_theory():
    client = make_client(consultation_route(), answer="Синглы звучат ярче, а хамбакеры плотнее.")

    result = interpret_query("Чем отличаются синглы от хамбакеров?", llm_client=client)

    assert result["mode"] == "consultation"
    assert "Синглы" in result["answer"]


def test_scenario_4_out_of_scope():
    client = make_client(
        {
            "intent": "off_topic",
            "enough_for_search": False,
            "missing_fields": [],
            "search_params": None,
            "should_offer_search": False,
        },
        answer="Я помогаю с гитарами и музыкальным оборудованием. Задайте вопрос по этой теме.",
    )

    result = interpret_query("Как сгенерировать картинку в Midjourney?", llm_client=client)

    assert result["mode"] == "consultation"
    assert "гитар" in result["answer"]


def test_scenario_5_acoustic():
    client = make_client(search_route({
        "search_queries": ["Yamaha F310", "Fender CD-60"],
        "price_max": 200,
        "type": "acoustic",
    }))

    result = interpret_query(
        "Нужна гитара для костра петь песни, недорогая, до 200 долларов.",
        llm_client=client,
        search_fn=mock_search,
    )

    assert result["mode"] == "search"
    assert result["search_params"]["price_max"] == 200


def test_scenario_6_contradiction():
    client = make_client(
        consultation_route(),
        answer="Акустических гитар с такой комплектацией не выпускают. Могу предложить электрогитару.",
    )

    result = interpret_query(
        "Хочу акустическую гитару с флойд роузом и активными звукоснимателями EMG.",
        llm_client=client,
    )

    assert result["mode"] == "consultation"
    assert "Акустических" in result["answer"]


def test_follow_up_consultation_allows_models_from_latest_search_history(monkeypatch):
    messages = [
        {
            "user_query": "Хочу телекастер",
            "mode": "search",
            "results": [
                {"title": "Fender Telecaster Deluxe Nashville 2021 - Daphne Blue", "price": 899},
                {"title": "Squier Classic Vibe '50s Telecaster 2024 - Butterscotch Blonde", "price": 429},
            ],
        }
    ]
    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: {})
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: messages)
    monkeypatch.setattr("backend.agent.context_manager.get_session_messages", lambda session_id: messages)
    client = make_client(
        consultation_route(offer=False),
        answer=(
            "Fender Telecaster Deluxe Nashville 2021 сильнее по универсальности, "
            "а Squier Classic Vibe '50s Telecaster 2024 проще и дешевле для старта."
        ),
    )

    result = interpret_query("а подскажи чем 1ый лучше 2го", llm_client=client, session_id=42)

    assert result["mode"] == "consultation"
    assert "Сейчас это выглядит как запрос на подбор" not in result["answer"]
    assert "Fender Telecaster Deluxe Nashville" in result["answer"]
    assert "Squier Classic Vibe" in result["answer"]


def test_follow_up_consultation_does_not_call_search(monkeypatch):
    messages = [
        {
            "user_query": "Хочу телекастер",
            "mode": "search",
            "results": [
                {"title": "Fender Player Telecaster", "price": 799},
                {"title": "Squier Classic Vibe Telecaster", "price": 429},
            ],
        }
    ]
    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: {})
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: messages)
    monkeypatch.setattr("backend.agent.context_manager.get_session_messages", lambda session_id: messages)
    client = make_client(
        consultation_route(offer=False),
        answer="Для новичка Squier Classic Vibe Telecaster проще по бюджету, Fender Player Telecaster дороже.",
    )
    search_fn = MagicMock(return_value=[])

    result = interpret_query(
        "для начала как новичку что лучше взять?",
        llm_client=client,
        search_fn=search_fn,
        session_id=42,
    )

    assert result["mode"] == "consultation"
    search_fn.assert_not_called()


def test_follow_up_consultation_does_not_append_search_offer(monkeypatch):
    messages = [
        {
            "user_query": "Хочу телекастер",
            "mode": "search",
            "results": [
                {"title": "Fender Player Telecaster", "price": 799},
                {"title": "Squier Classic Vibe Telecaster", "price": 429},
            ],
        }
    ]
    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: {})
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: messages)
    monkeypatch.setattr("backend.agent.context_manager.get_session_messages", lambda session_id: messages)
    client = make_client(
        consultation_route(offer=False),
        answer="Из этих Squier Classic Vibe Telecaster логичнее для новичка.",
    )

    result = interpret_query("что новичку взять из этих?", llm_client=client, session_id=42)

    assert "Reverb" not in result["answer"]
    assert "ссыл" not in result["answer"].lower()


def test_consultation_sanitizer_blocks_models_not_in_latest_search_history(monkeypatch):
    messages = [
        {
            "user_query": "Хочу лес пол",
            "mode": "search",
            "results": [{"title": "Gibson Les Paul Tribute", "price": 999}],
        },
        {
            "user_query": "Хочу телекастер",
            "mode": "search",
            "results": [{"title": "Squier Classic Vibe Telecaster", "price": 429}],
        },
    ]
    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: {})
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: messages)
    monkeypatch.setattr("backend.agent.context_manager.get_session_messages", lambda session_id: messages)
    client = make_client(
        consultation_route(offer=False),
        answer=(
            "Из текущих вариантов Squier Classic Vibe Telecaster норм для старта, "
            "а Gibson Les Paul Tribute можно взять как более плотный каталоговый вариант."
        ),
    )

    result = interpret_query("что новичку взять?", llm_client=client, session_id=42)

    assert result["mode"] == "consultation"
    assert "#1" in result["answer"]
    assert "Сейчас это выглядит" not in result["answer"]


def test_misrouted_beginner_recommendation_catalog_block_returns_clarification():
    client = make_client(
        consultation_route(offer=False),
        answer="Для новичка подойдут Yamaha Pacifica 112V и Squier Affinity Stratocaster.",
    )
    client.ask.side_effect = [
        "Для новичка подойдут Yamaha Pacifica 112V и Squier Affinity Stratocaster.",
        "Скажите бюджет; тип можно не выбирать, я подберу широкий вариант.",
    ]

    result = interpret_query("хорошую гитарку для новичка посоветуй давай", llm_client=client)

    assert result["mode"] == "clarification"
    assert "бюджет" in result["question"].lower()
    assert "тип можно не выбирать" in result["question"].lower()
    assert "Сейчас это выглядит" not in str(result)


def test_sanitizer_recovery_clarification_saves_search_state(monkeypatch):
    saved_states = []
    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: {})
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: [])
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: saved_states.append(state))
    client = make_client(
        consultation_route(offer=False),
        answer="Для новичка подойдут Yamaha Pacifica 112V и Squier Affinity Stratocaster.",
    )
    client.ask.side_effect = [
        "Для новичка подойдут Yamaha Pacifica 112V и Squier Affinity Stratocaster.",
        "Скажите бюджет; тип можно не выбирать.",
    ]

    result = interpret_query("хорошую гитарку для новичка посоветуй давай", llm_client=client, session_id=42)

    assert result["mode"] == "clarification"
    assert saved_states[-1]["last_intent"] == "search"
    assert saved_states[-1]["missing_fields"] == ["budget", "type"]
    assert saved_states[-1]["asked_fields"] == ["budget", "type"]


def test_sanitizer_block_with_latest_titles_returns_current_options_message(monkeypatch):
    messages = [
        {
            "user_query": "Хочу телекастер",
            "mode": "search",
            "results": [{"title": "Squier Classic Vibe Telecaster", "price": 429}],
        },
    ]
    monkeypatch.setattr("backend.agent.service.get_session_state", lambda session_id: {})
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: messages)
    monkeypatch.setattr("backend.agent.context_manager.get_session_messages", lambda session_id: messages)
    client = make_client(
        consultation_route(offer=False),
        answer=(
            "Squier Classic Vibe Telecaster норм из текущей выдачи, "
            "а Yamaha Pacifica 112V можно взять как другой вариант."
        ),
    )

    result = interpret_query("что новичку взять?", llm_client=client, session_id=42)

    assert result["mode"] == "consultation"
    assert "#1" in result["answer"]
    assert "Сейчас это выглядит" not in result["answer"]


def test_consultation_sanitizer_blocks_single_invented_model_without_latest_search():
    answer = "Для новичка я бы взял Yamaha Pacifica 112V."

    assert _looks_like_catalog_content(answer, allowed_titles=[]) is True


def test_consultation_sanitizer_allows_bare_brand_discussion():
    answer = "Fender обычно ярче, Gibson обычно плотнее."

    assert _looks_like_catalog_content(answer, allowed_titles=[]) is False


def test_router_history_serializes_search_results_as_numbered_context(monkeypatch):
    messages = [
        {
            "user_query": "Хочу телекастер",
            "mode": "search",
            "results": [
                {"title": "Fender Telecaster Deluxe Nashville 2021 - Daphne Blue", "price": 899},
                {"title": "Squier Classic Vibe '50s Telecaster 2024 - Butterscotch Blonde", "price": 429},
            ],
        }
    ]
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: messages)

    history = _build_router_history(42)

    assert history[1]["content"] == (
        "Последняя поисковая выдача:\n"
        "#1 Fender Telecaster Deluxe Nashville 2021 - Daphne Blue, $899\n"
        "#2 Squier Classic Vibe '50s Telecaster 2024 - Butterscotch Blonde, $429"
    )


def test_router_history_keeps_latest_search_context_outside_recent_tail(monkeypatch):
    messages = [
        {
            "user_query": "Хочу телекастер",
            "mode": "search",
            "results": [
                {"title": "Fender Player Telecaster", "price": 799},
                {"title": "Squier Classic Vibe Telecaster", "price": 429},
            ],
        },
        *[
            {
                "user_query": f"уточнение {index}",
                "mode": "consultation",
                "answer": f"ответ {index}",
            }
            for index in range(7)
        ],
    ]
    monkeypatch.setattr("backend.agent.service.get_session_messages", lambda session_id: messages)

    history = _build_router_history(42)
    contents = [message["content"] for message in history]

    assert any("Последняя поисковая выдача:" in content for content in contents)
    assert any("#1 Fender Player Telecaster, $799" in content for content in contents)
