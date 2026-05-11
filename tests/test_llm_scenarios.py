"""Сценарные тесты LLM-router с параметризацией."""

import pytest

from backend.agent.service import InvalidRouterResponseError, interpret_query


class ScenarioClient:
    def __init__(self, route_plan, answer="Ответ консультации"):
        self.route_plan = route_plan
        self.answer = answer

    def classify_and_plan_query(self, query, history=None, current_state=None):
        if isinstance(self.route_plan, Exception):
            raise self.route_plan
        return self.route_plan

    def ask(self, query, prompt, history=None):
        return self.answer


def search_route(search_params):
    return {
        "intent": "search",
        "enough_for_search": True,
        "missing_fields": [],
        "search_params": search_params,
        "should_offer_search": False,
    }


def consultation_route():
    return {
        "intent": "consultation",
        "enough_for_search": False,
        "missing_fields": [],
        "search_params": None,
        "should_offer_search": False,
    }


scenarios = [
    (
        "Привет! Ищу яркую электрогитару для блюза и фанка, бюджет до 1000 баксов.",
        search_route({
            "search_queries": ["Fender Player Stratocaster", "Squier Classic Vibe Telecaster"],
            "price_max": 1000,
            "style": "blues",
            "sound": "bright",
        }),
        "search",
    ),
    (
        "Чем отличаются синглы от хамбакеров?",
        consultation_route(),
        "consultation",
    ),
    (
        "Как сгенерировать картинку в Midjourney?",
        {
            "intent": "off_topic",
            "enough_for_search": False,
            "missing_fields": [],
            "search_params": None,
            "should_offer_search": False,
        },
        "consultation",
    ),
    (
        "Нужна гитара для костра петь песни, недорогая, до 200 долларов.",
        search_route({
            "search_queries": ["Yamaha F310", "Fender CD-60", "Epiphone DR-100"],
            "price_max": 200,
            "type": "acoustic",
        }),
        "search",
    ),
]


@pytest.mark.parametrize("query, route_plan, expected_mode", scenarios)
def test_interpret_query_scenarios(query, route_plan, expected_mode):
    result = interpret_query(
        query,
        llm_client=ScenarioClient(route_plan, answer="Синглы ярче"),
        search_fn=lambda *args: [{"title": "Guitar", "price": 100}],
    )

    assert result["mode"] == expected_mode
    if expected_mode == "search":
        assert "search_params" in result
    else:
        assert "answer" in result


def test_invalid_router_response_is_error():
    with pytest.raises(InvalidRouterResponseError):
        interpret_query("Сломани запрос", llm_client=ScenarioClient({"intent": "search"}))
