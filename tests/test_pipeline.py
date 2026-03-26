"""Тесты полного пайплайна interpret_query с mock-данными."""

import os
from unittest.mock import MagicMock, patch

import pytest

from backend.agent.service import interpret_query


class MockLLMClient:
    """Мок LLM-клиента для тестов."""

    def __init__(self, consultation_answer="Тестовый ответ консультанта", search_params=None):
        self.consultation_answer = consultation_answer
        self.search_params = search_params or {
            "search_queries": ["Fender Stratocaster"],
            "price_min": None,
            "price_max": 1000,
        }

    def ask(self, text: str, system_prompt: str) -> str:
        return self.consultation_answer

    def extract_search_params(self, text: str) -> dict:
        return self.search_params


def mock_search_fn(search_queries, price_min=None, price_max=None):
    """Мок функции поиска — возвращает фиксированные результаты."""
    return [
        {
            "id": "1",
            "title": "Fender Stratocaster MIM",
            "price": 800,
            "currency": "USD",
            "image_url": "https://example.com/img1.jpg",
            "listing_url": "https://reverb.com/item/1",
        },
        {
            "id": "2",
            "title": "Fender Stratocaster Player",
            "price": 950,
            "currency": "USD",
            "image_url": "https://example.com/img2.jpg",
            "listing_url": "https://reverb.com/item/2",
        },
    ]


def test_consultation_with_mock():
    """Consultation с mock LLM → answer + on_status вызван."""
    mock_llm = MockLLMClient(consultation_answer="Хамбакеры дают более плотный звук.")
    statuses = []

    result = interpret_query(
        text="В чем разница между single-coil и humbucker?",
        llm_client=mock_llm,
        on_status=lambda s: statuses.append(s),
    )

    assert result["mode"] == "consultation"
    assert result["answer"] == "Хамбакеры дают более плотный звук."
    assert "Определяю режим..." in statuses
    assert "Формирую ответ..." in statuses


def test_search_with_mock():
    """Search с mock LLM + mock search → results через ranking + on_status на каждом шаге."""
    mock_llm = MockLLMClient(
        search_params={
            "search_queries": ["Fender Stratocaster"],
            "price_min": None,
            "price_max": 1000,
        }
    )
    statuses = []

    result = interpret_query(
        text="Найди Fender Stratocaster до 1000$",
        llm_client=mock_llm,
        search_fn=mock_search_fn,
        on_status=lambda s: statuses.append(s),
    )

    assert result["mode"] == "search"
    assert isinstance(result["results"], list)
    assert len(result["results"]) > 0

    # Проверяем порядок статусов
    expected_statuses = [
        "Определяю режим...",
        "Генерирую параметры поиска...",
        "Ищу на Reverb...",
        "Ранжирую результаты...",
    ]
    assert statuses == expected_statuses


def test_no_api_key_fallback():
    """Без API ключа → не падает, возвращает fallback."""
    # Убираем переменную окружения
    env_backup = os.environ.pop("GROQ_API_KEY", None)
    try:
        statuses = []
        result = interpret_query(
            text="В чем разница между гитарами?",
            llm_client=None,
            on_status=lambda s: statuses.append(s),
        )

        assert result["mode"] == "consultation"
        assert "answer" in result
        assert len(result["answer"]) > 0
    finally:
        # Восстанавливаем переменную
        if env_backup is not None:
            os.environ["GROQ_API_KEY"] = env_backup


def test_without_on_status():
    """Без on_status → работает без ошибок (обратная совместимость)."""
    mock_llm = MockLLMClient()

    # Consultation без on_status
    result = interpret_query(
        text="Что такое P90?",
        llm_client=mock_llm,
    )
    assert result["mode"] == "consultation"
    assert "answer" in result

    # Search без on_status
    result = interpret_query(
        text="Найди Gibson Les Paul до 2000$",
        llm_client=mock_llm,
        search_fn=mock_search_fn,
    )
    assert result["mode"] == "search"
    assert "results" in result
