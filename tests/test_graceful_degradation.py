"""Тесты graceful degradation — проверка устойчивости пайплайна к ошибкам."""

import os
from unittest.mock import patch, MagicMock

import pytest

from backend.agent.service import interpret_query


class MockLLMClient:
    """Мок LLM-клиента для тестов."""

    def ask(self, text: str, system_prompt: str) -> str:
        return "Тестовый ответ консультанта."

    def extract_search_params(self, text: str) -> dict:
        return {
            "search_queries": ["Fender Stratocaster"],
            "price_min": None,
            "price_max": 1000,
        }


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


class TestDetectModeFailure:
    """detect_mode бросает Exception → fallback на consultation."""

    def test_detect_mode_exception_falls_back_to_consultation(self):
        """Если detect_mode падает — режим consultation."""
        with patch("backend.agent.service.detect_mode", side_effect=RuntimeError("mode detection broken")):
            result = interpret_query(
                text="Что угодно",
                llm_client=MockLLMClient(),
            )

        assert result["mode"] == "consultation"
        assert "answer" in result


class TestNoApiKey:
    """Без GROQ_API_KEY → pipeline работает в degraded mode."""

    def test_no_api_key_consultation_returns_fallback_message(self):
        """Consultation без API ключа → сообщение о недоступности."""
        env_backup = os.environ.pop("GROQ_API_KEY", None)
        try:
            result = interpret_query(
                text="Что такое хамбакер?",
                llm_client=None,
            )
            assert result["mode"] == "consultation"
            assert "answer" in result
            assert len(result["answer"]) > 0
        finally:
            if env_backup is not None:
                os.environ["GROQ_API_KEY"] = env_backup

    def test_no_api_key_search_uses_text_as_query(self):
        """Search без API ключа → текст запроса используется как search_queries."""
        env_backup = os.environ.pop("GROQ_API_KEY", None)
        try:
            result = interpret_query(
                text="Найди Fender Stratocaster",
                llm_client=None,
                search_fn=mock_search_fn,
            )
            assert result["mode"] == "search"
            assert isinstance(result["results"], list)
        finally:
            if env_backup is not None:
                os.environ["GROQ_API_KEY"] = env_backup
