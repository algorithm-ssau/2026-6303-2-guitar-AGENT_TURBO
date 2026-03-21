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
