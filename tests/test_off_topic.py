"""Тесты off-topic через LLM-router contract."""

from unittest.mock import MagicMock

import pytest

from backend.agent.service import InvalidRouterResponseError, get_off_topic_prompt, interpret_query


def test_off_topic_uses_generated_refusal_prompt():
    mock_llm = MagicMock()
    mock_llm.classify_and_plan_query.return_value = {
        "intent": "off_topic",
        "enough_for_search": False,
        "missing_fields": [],
        "search_params": None,
        "should_offer_search": False,
    }
    mock_llm.ask.return_value = "Я помогаю с гитарами и музыкальным оборудованием. Задайте вопрос по этой теме."

    result = interpret_query("напиши сортировку пузырьком", llm_client=mock_llm)

    assert result == {
        "mode": "consultation",
        "answer": "Я помогаю с гитарами и музыкальным оборудованием. Задайте вопрос по этой теме.",
    }
    mock_llm.ask.assert_called_once()
    _, prompt = mock_llm.ask.call_args.args[:2]
    assert prompt == get_off_topic_prompt()


@pytest.mark.parametrize(
    "bad_answer",
    [
        "```python\nprint('bubble sort')\n```",
        "1. Сравниваем элементы\n2. Меняем местами",
        "- Вот шаги сортировки",
        "Смотрите https://example.com",
    ],
)
def test_off_topic_rejects_unsafe_generated_answer(bad_answer):
    mock_llm = MagicMock()
    mock_llm.classify_and_plan_query.return_value = {
        "intent": "off_topic",
        "enough_for_search": False,
        "missing_fields": [],
        "search_params": None,
        "should_offer_search": False,
    }
    mock_llm.ask.return_value = bad_answer

    with pytest.raises(InvalidRouterResponseError):
        interpret_query("напиши сортировку пузырьком", llm_client=mock_llm)
