import pytest

from backend.agent.service import (
    InvalidRouterResponseError,
    LLMUnavailableError,
    _classify_query,
    interpret_query,
)
from backend.agent.llm_client import _build_router_prompt


class FakeRouterClient:
    def __init__(self, route_plan, answer="Консультационный ответ."):
        self.route_plan = route_plan
        self.answer = answer

    def classify_and_plan_query(self, user_message, history=None, current_state=None):
        return self.route_plan

    def ask(self, user_message, system_prompt, history=None):
        return self.answer


def test_search_uses_router_params_and_returns_search_params():
    client = FakeRouterClient({
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {
            "search_queries": ["Fender Telecaster"],
            "price_min": None,
            "price_max": 800,
            "type": "telecaster",
            "brand": "Fender",
            "pickups": "single_coil",
            "sound": "bright",
            "style": "country",
        },
        "should_offer_search": False,
    })

    def search_fn(queries, price_min, price_max):
        assert queries == ["Fender Telecaster"]
        assert price_max == 800
        return [{
            "id": "1",
            "title": "Fender Player Telecaster",
            "price": 700,
            "currency": "USD",
            "listing_url": "https://reverb.com/item/1",
            "image_url": "https://reverb.com/img/1.jpg",
        }]

    result = interpret_query("Подбери Telecaster до 800$", llm_client=client, search_fn=search_fn)

    assert result["mode"] == "search"
    assert result["search_params"]["type"] == "telecaster"
    assert result["search_params"]["price_max"] == 800


def test_type_any_is_user_facing_but_not_execution_type(monkeypatch):
    client = FakeRouterClient({
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": {
            "search_queries": ["funk electric guitar"],
            "price_min": None,
            "price_max": 500,
            "type": "any",
            "brand": None,
            "pickups": "single_coil",
            "sound": "bright",
            "style": "funk",
        },
        "should_offer_search": False,
    })

    captured = {}

    def fake_rank(results, params):
        captured["rank_params"] = params
        return results

    monkeypatch.setattr("backend.agent.service.rank_results", fake_rank)

    result = interpret_query(
        "тип не важен, бюджет до 500",
        llm_client=client,
        search_fn=lambda queries, price_min, price_max: [{"title": "Any Guitar", "price": 400}],
    )

    assert result["search_params"]["type"] == "any"
    assert captured["rank_params"]["type"] is None


def test_consultation_uses_separate_answer_prompt():
    client = FakeRouterClient({
        "intent": "consultation",
        "enough_for_search": False,
        "missing_fields": [],
        "search_params": None,
        "should_offer_search": True,
    }, answer="P90 звучат ярче хамбакеров.")

    result = interpret_query("Чем отличаются P90 от хамбакеров?", llm_client=client)

    assert result["mode"] == "consultation"
    assert "P90" in result["answer"]
    assert "подобрать" in result["answer"].lower()


def test_off_topic_uses_generated_refusal_answer():
    client = FakeRouterClient({
        "intent": "off_topic",
        "enough_for_search": False,
        "missing_fields": [],
        "search_params": None,
        "should_offer_search": False,
    }, answer="Я помогаю с гитарами и музыкальным оборудованием. Задайте вопрос по этой теме.")

    result = interpret_query("напиши сортировку пузырьком", llm_client=client)

    assert result["mode"] == "consultation"
    assert result["answer"] == "Я помогаю с гитарами и музыкальным оборудованием. Задайте вопрос по этой теме."


def test_invalid_router_shape_raises_error():
    client = FakeRouterClient({"intent": "search", "missing_fields": []})

    with pytest.raises(InvalidRouterResponseError):
        interpret_query("Подбери гитару", llm_client=client)


def test_router_repair_fills_required_search_queries_without_backend_inference():
    class RepairingClient:
        def __init__(self):
            self.repair_calls = []

        def classify_and_plan_query(self, user_message, history=None, current_state=None):
            return {
                "intent": "search",
                "enough_for_search": True,
                "missing_fields": [],
                "search_params": {
                    "search_queries": [],
                    "price_min": None,
                    "price_max": 600,
                    "type": "telecaster",
                    "brand": None,
                    "pickups": None,
                    "sound": "bright",
                    "style": None,
                },
                "should_offer_search": False,
            }

        def repair_router_plan(self, user_message, invalid_plan, validation_errors, history=None, current_state=None):
            self.repair_calls.append((invalid_plan, validation_errors))
            return {
                "intent": "search",
                "enough_for_search": True,
                "missing_fields": [],
                "search_params": {
                    "search_queries": ["Fender Telecaster", "Squier Classic Vibe Telecaster"],
                    "price_min": None,
                    "price_max": 600,
                    "type": "telecaster",
                    "brand": None,
                    "pickups": None,
                    "sound": "bright",
                    "style": None,
                },
                "should_offer_search": False,
            }

    client = RepairingClient()
    result = interpret_query(
        "Хочу телекастер с ярким звуком, до $600",
        llm_client=client,
        search_fn=lambda queries, price_min, price_max: [{"title": "Tele", "price": 500}],
    )

    assert result["mode"] == "search"
    assert client.repair_calls
    assert any("search_queries" in error for error in client.repair_calls[0][1])


def test_router_repair_skips_non_repairable_invalid_intent():
    class Client:
        repair_called = False

        def classify_and_plan_query(self, user_message, history=None, current_state=None):
            return {"intent": "unknown", "missing_fields": [], "search_params": None}

        def repair_router_plan(self, *args, **kwargs):
            self.repair_called = True
            return {}

    client = Client()

    with pytest.raises(InvalidRouterResponseError):
        interpret_query("Подбери гитару", llm_client=client)

    assert client.repair_called is False


def test_router_repair_provider_exception_raises_llm_unavailable():
    class Client:
        def classify_and_plan_query(self, user_message, history=None, current_state=None):
            return {
                "intent": "search",
                "enough_for_search": True,
                "missing_fields": [],
                "search_params": {"search_queries": []},
                "should_offer_search": False,
            }

        def repair_router_plan(self, *args, **kwargs):
            raise RuntimeError("upstream repair failed")

    with pytest.raises(LLMUnavailableError):
        interpret_query("Хочу телекастер до 600", llm_client=Client())


def test_router_repair_rejects_changed_valid_intent():
    class Client:
        def classify_and_plan_query(self, user_message, history=None, current_state=None):
            return {
                "intent": "search",
                "enough_for_search": True,
                "missing_fields": [],
                "search_params": {"search_queries": []},
                "should_offer_search": False,
            }

        def repair_router_plan(self, *args, **kwargs):
            return {
                "intent": "consultation",
                "enough_for_search": False,
                "missing_fields": [],
                "search_params": None,
                "should_offer_search": True,
            }

    with pytest.raises(InvalidRouterResponseError):
        interpret_query("Хочу телекастер до 600", llm_client=Client())


def test_router_repair_oversized_prompt_is_not_sent(monkeypatch):
    class Client:
        repair_called = False

        def classify_and_plan_query(self, user_message, history=None, current_state=None):
            return {
                "intent": "search",
                "enough_for_search": True,
                "missing_fields": [],
                "search_params": {"search_queries": []},
                "should_offer_search": False,
            }

        def repair_router_plan(self, *args, **kwargs):
            self.repair_called = True
            return {}

    client = Client()
    monkeypatch.setattr("backend.agent.service._router_max_prompt_chars", lambda: 1)

    with pytest.raises(InvalidRouterResponseError):
        _classify_query(
            "Хочу телекастер до 600",
            client,
            history=[],
            current_state={},
            repair_histories=[("stateless", [])],
        )

    assert client.repair_called is False


def test_incomplete_search_route_with_null_search_params_does_not_call_repair():
    class Client:
        def __init__(self):
            self.repair_called = False

        def classify_and_plan_query(self, user_message, history=None, current_state=None):
            return {
                "intent": "search",
                "enough_for_search": False,
                "missing_fields": ["budget", "type"],
                "search_params": None,
                "should_offer_search": False,
            }

        def ask(self, user_message, system_prompt, history=None):
            return "Скажите бюджет; тип можно не выбирать."

        def repair_router_plan(self, *args, **kwargs):
            self.repair_called = True
            return {}

    client = Client()
    result = interpret_query("хорошую гитарку для новичка посоветуй давай", llm_client=client)

    assert result["mode"] == "clarification"
    assert client.repair_called is False


def test_accept_beginner_budget_without_pending_state_is_invalid():
    client = FakeRouterClient({
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "default_actions": ["accept_beginner_budget"],
        "search_params": {
            "search_queries": ["beginner electric guitar"],
            "price_min": None,
            "price_max": None,
            "type": "any",
        },
        "should_offer_search": False,
    })

    with pytest.raises(InvalidRouterResponseError):
        interpret_query("да", llm_client=client)


def test_accept_beginner_budget_with_reset_is_invalid_even_with_pending_state(monkeypatch):
    monkeypatch.setattr(
        "backend.agent.service.get_session_state",
        lambda session_id: {"pending_defaults": {"budget": {"kind": "beginner_cheap", "price_max": 500}}},
    )
    monkeypatch.setattr("backend.agent.service.save_session_state", lambda session_id, state: None)
    client = FakeRouterClient({
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "default_actions": ["accept_beginner_budget"],
        "state_action": "reset",
        "search_params": {
            "search_queries": ["beginner electric guitar"],
            "price_min": None,
            "price_max": None,
            "type": "any",
        },
        "should_offer_search": False,
    })

    with pytest.raises(InvalidRouterResponseError):
        interpret_query("да", llm_client=client, session_id=42)


def test_missing_llm_raises_unavailable(monkeypatch):
    monkeypatch.setattr("backend.agent.service.create_llm_client", lambda: None)

    with pytest.raises(LLMUnavailableError):
        interpret_query("Подбери гитару")


def test_router_prompt_documents_follow_up_consultation_examples():
    prompt = _build_router_prompt("чем 1ый лучше 2го", "", {})

    assert "Последняя поисковая выдача" in prompt
    assert "для новичка что лучше взять" in prompt
    assert '"intent":"consultation"' in prompt
    assert '"should_offer_search":false' in prompt
    assert "покажи ещё до 1000" in prompt
    assert '"intent":"search"' in prompt


def test_router_prompt_routes_concrete_beginner_recommendation_to_search_clarification():
    prompt = _build_router_prompt("хорошую гитарку для новичка посоветуй давай", "", {})

    assert "хорошую гитарку для новичка посоветуй" in prompt
    assert '"intent":"search"' in prompt
    assert '"enough_for_search":false' in prompt
    assert '"missing_fields":["budget","type"]' in prompt


def test_router_prompt_distinguishes_beginner_recommendation_without_and_with_search_context():
    prompt = _build_router_prompt("для начала как новичку что лучше взять?", "", {})

    assert "No previous search context" in prompt
    assert '=> search' in prompt
    assert 'With "Последняя поисковая выдача"' in prompt
    assert '=> consultation' in prompt


def test_router_prompt_documents_no_preference_and_default_actions():
    prompt = _build_router_prompt("хочу гитару, я новичок, ничего не понимаю, без лишних вопросов", "", {})

    assert "no_preference_fields" in prompt
    assert "default_actions" in prompt
    assert "apply_beginner_budget" in prompt
    assert "accept_beginner_budget" in prompt
    assert "state_action" in prompt
