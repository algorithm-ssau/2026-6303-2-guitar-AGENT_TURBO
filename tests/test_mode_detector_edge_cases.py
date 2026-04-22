"""Тесты граничных случаев для детектора режима."""

import pytest
from backend.agent.mode_detector import detect_mode


def test_mixed_request_returns_search():
    """Смешанный запрос (купить + объяснить) → приоритет search."""
    assert detect_mode("хочу купить и расскажи о датчиках") == "search"


def test_empty_string_returns_consultation():
    """Пустая строка → consultation (безопасный дефолт)."""
    assert detect_mode("") == "consultation"


def test_very_short_query_returns_consultation():
    """Очень короткий запрос без намерения → consultation."""
    assert detect_mode("гитара?") == "consultation"


def test_whitespace_only_returns_consultation():
    """Строка из пробелов → consultation."""
    assert detect_mode("   ") == "consultation"


def test_written_above_with_previous_search_returns_search():
    """Ссылка на предыдущий поиск должна оставаться в search-контексте."""
    assert detect_mode("я же писал выше", has_previous_search=True) == "search"


@pytest.mark.parametrize(
    "query",
    [
        "покажи ссылки",
        "дай ссылки",
        "дай ссылки на них",
        "покажи примеры моделей",
        "перейди в режим примеров",
    ],
)
def test_link_requests_are_search_signals(query: str):
    """Запрос ссылок должен вести в search, а не в свободную консультацию."""
    assert detect_mode(query) == "search"


@pytest.mark.parametrize(
    "query, expected_mode",
    [
        # Дополнительные примеры из таблицы MODE_DETECTION.md
        (
            "Подскажи Telecaster до 1500$, но сначала коротко объясни отличия от Strat.",
            "search",
        ),
        (
            "Сделай подборку гитар для фанка с ярким звуком.",
            "search",
        ),
        (
            "Почему P90 считают компромиссом между single и humbucker?",
            "consultation",
        ),
    ],
    ids=[
        "mixed_telecaster_search",
        "funk_collection_search",
        "p90_compromise_consultation",
    ],
)
def test_additional_examples(query: str, expected_mode: str):
    """Дополнительные примеры из таблицы классификации."""
    assert detect_mode(query) == expected_mode
