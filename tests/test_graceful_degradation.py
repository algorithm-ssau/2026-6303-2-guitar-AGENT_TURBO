"""Тесты graceful degradation — проверка устойчивости пайплайна к ошибкам."""

import sys
from unittest.mock import patch, MagicMock

import pytest

# Mock groq, чтобы тесты работали без установленного пакета
if "groq" not in sys.modules:
    sys.modules["groq"] = MagicMock()

from backend.agent.service import LLMUnavailableError, interpret_query


class MockLLMClient:
    """Мок LLM-клиента для тестов."""

    def classify_and_plan_query(self, text: str, history=None, current_state=None) -> dict:
        return {
            "intent": "search",
            "enough_for_search": True,
            "missing_fields": [],
            "search_params": {
                "search_queries": ["Fender Stratocaster"],
                "price_min": None,
                "price_max": 1000,
                "type": "stratocaster",
                "brand": None,
                "pickups": None,
                "sound": None,
                "style": None,
            },
            "should_offer_search": False,
        }

    def ask(self, text: str, system_prompt: str, history=None) -> str:
        return "Тестовый ответ консультанта."


def mock_search_fn(search_queries, price_min=None, price_max=None):
    """Мок функции поиска — возвращает фиксированные результаты."""
    return [
        {"id": str(i), "title": f"Guitar {i}", "price": 100 * i,
         "currency": "USD", "image_url": f"https://example.com/{i}.jpg",
         "listing_url": f"https://reverb.com/item/{i}"}
        for i in range(1, 8)
    ]


class TestSearchReverbFailure:
    """search_reverb бросает Exception → fallback, не crash."""

    def test_search_reverb_exception_returns_empty_results(self):
        """Если search_reverb падает — возвращаем пустые results с ошибкой."""
        def failing_search(*args, **kwargs):
            raise ConnectionError("Reverb API недоступен")

        result = interpret_query(
            text="Найди Fender Stratocaster",
            llm_client=MockLLMClient(),
            search_fn=failing_search,
        )

        assert result["mode"] == "search"
        assert result["results"] == []
        assert "error" in result


class TestRankResultsFailure:
    """rank_results бросает Exception → неранжированные первые 5."""

    def test_rank_results_exception_returns_unranked(self):
        """Если rank_results падает — возвращаем первые 5 неранжированных."""
        with patch("backend.agent.service.rank_results", side_effect=RuntimeError("ranking broken")):
            result = interpret_query(
                text="Найди Gibson Les Paul",
                llm_client=MockLLMClient(),
                search_fn=mock_search_fn,
            )

        assert result["mode"] == "search"
        assert isinstance(result["results"], list)
        assert len(result["results"]) == 5
        # Первые 5 из 7 — неранжированные
        assert result["results"][0]["title"] == "Guitar 1"
        assert result["results"][4]["title"] == "Guitar 5"


class TestRouterFailure:
    """LLM-router errors are explicit service errors."""

    def test_router_exception_raises_unavailable(self):
        mock_client = MockLLMClient()
        mock_client.classify_and_plan_query = MagicMock(side_effect=RuntimeError("router broken"))

        with pytest.raises(LLMUnavailableError):
            interpret_query(text="Что угодно", llm_client=mock_client)

    def test_off_topic_refusal_generation_error_raises_unavailable(self):
        mock_client = MagicMock()
        mock_client.classify_and_plan_query.return_value = {
            "intent": "off_topic",
            "enough_for_search": False,
            "missing_fields": [],
            "search_params": None,
            "should_offer_search": False,
        }
        mock_client.ask.return_value = "Error: upstream unavailable"

        with pytest.raises(LLMUnavailableError):
            interpret_query(text="напиши сортировку пузырьком", llm_client=mock_client)


class TestNoApiKey:
    """Без GROQ_API_KEY → нет regex fallback."""

    def test_no_api_key_consultation_raises_unavailable(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(LLMUnavailableError):
            interpret_query(text="Что такое хамбакер?", llm_client=None)

    def test_no_api_key_search_raises_unavailable(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(LLMUnavailableError):
            interpret_query(text="Найди Fender Stratocaster", llm_client=None, search_fn=mock_search_fn)
