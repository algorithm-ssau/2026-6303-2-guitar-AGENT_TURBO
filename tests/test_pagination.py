"""Тесты пагинации сессий."""

import pytest

from backend.history.service import create_session, get_sessions, clear_history, init_db


@pytest.fixture(autouse=True)
def clean_db():
    """Инициализируем БД и очищаем историю перед каждым тестом."""
    init_db()
    clear_history()
    yield


def _create_n_sessions(n: int):
    """Создать N сессий."""
    for i in range(n):
        create_session(f"Session {i}")


def test_limit_returns_max_sessions():
    """limit=3 при 10 сессиях → 3 сессии, total=10."""
    _create_n_sessions(10)
    sessions, total = get_sessions(limit=3)
    assert len(sessions) == 3
    assert total == 10


def test_offset_returns_next_page():
    """offset=3, limit=3 → следующие 3 сессии."""
    _create_n_sessions(10)
    first_page, total1 = get_sessions(limit=3, offset=0)
    second_page, total2 = get_sessions(limit=3, offset=3)

    assert len(second_page) == 3
    assert total2 == 10
    # Страницы не пересекаются
    first_ids = {s["id"] for s in first_page}
    second_ids = {s["id"] for s in second_page}
    assert first_ids.isdisjoint(second_ids)


def test_offset_beyond_total_returns_empty():
    """offset > total → пустой список, total корректный."""
    _create_n_sessions(5)
    sessions, total = get_sessions(offset=100, limit=10)
    assert len(sessions) == 0
    assert total == 5


def test_default_params_first_page():
    """Без параметров → первые 20 сессий."""
    _create_n_sessions(30)
    sessions, total = get_sessions()
    assert len(sessions) == 20
    assert total == 30


def test_total_across_pages():
    """total одинаковый на всех страницах."""
    _create_n_sessions(7)
    _, total1 = get_sessions(limit=3, offset=0)
    _, total2 = get_sessions(limit=3, offset=3)
    _, total3 = get_sessions(limit=3, offset=6)
    assert total1 == total2 == total3 == 7
