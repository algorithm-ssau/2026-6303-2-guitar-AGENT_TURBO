"""Тесты эндпоинта GET /api/stats и функции get_stats()."""

import os
import sqlite3
import pytest

from backend.history.stats import get_stats


@pytest.fixture
def clean_db(tmp_path):
    """Фикстура: временная БД для изолированных тестов."""
    db_path = str(tmp_path / "test_stats.db")

    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            user_query TEXT NOT NULL,
            mode       TEXT NOT NULL,
            answer     TEXT,
            results    TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );
    """)
    conn.commit()
    conn.close()

    # Установим путь к БД для stats
    old_path = os.environ.get("CHAT_DB_PATH")
    os.environ["CHAT_DB_PATH"] = db_path

    # Сбросим кэш
    import backend.history.stats as stats_module
    stats_module._DB_PATH = None

    yield db_path

    # Cleanup
    if old_path is not None:
        os.environ["CHAT_DB_PATH"] = old_path
    else:
        os.environ.pop("CHAT_DB_PATH", None)
    stats_module._DB_PATH = None


@pytest.fixture
def populated_db(clean_db):
    """Фикстура: БД с тестовыми данными."""
    db_path = clean_db

    conn = sqlite3.connect(db_path)
    # Сессия 1: 2 search
    conn.execute("INSERT INTO sessions (title) VALUES (?)", ("Fender Strat",))
    conn.execute(
        "INSERT INTO chat_history (session_id, user_query, mode, answer, results) VALUES (?, ?, ?, ?, ?)",
        (1, "Fender Stratocaster", "search", "Вот варианты", "[]"),
    )
    conn.execute(
        "INSERT INTO chat_history (session_id, user_query, mode, answer, results) VALUES (?, ?, ?, ?, ?)",
        (1, "Gibson Les Paul", "search", "Ещё варианты", "[]"),
    )

    # Сессия 2: 1 search + 1 consultation
    conn.execute("INSERT INTO sessions (title) VALUES (?)", ("Consultation",))
    conn.execute(
        "INSERT INTO chat_history (session_id, user_query, mode, answer, results) VALUES (?, ?, ?, ?, ?)",
        (2, "Strat для фанка", "search", "Ищу", "[]"),
    )
    conn.execute(
        "INSERT INTO chat_history (session_id, user_query, mode, answer, results) VALUES (?, ?, ?, ?, ?)",
        (2, "Как выбрать медиатор?", "consultation", "Подбирайте по толщине", None),
    )

    # Сессия 3: 1 off_topic
    conn.execute("INSERT INTO sessions (title) VALUES (?)", ("Off topic",))
    conn.execute(
        "INSERT INTO chat_history (session_id, user_query, mode, answer, results) VALUES (?, ?, ?, ?, ?)",
        (3, "Привет", "off_topic", "Привет!", None),
    )
    conn.commit()
    conn.close()

    return db_path


class TestGetStats:
    """Тесты функции get_stats()."""

    def test_empty_db_returns_zeros(self, clean_db):
        """Пустая БД → все метрики = 0."""
        stats = get_stats()

        assert stats["total_sessions"] == 0
        assert stats["total_queries"] == 0
        assert stats["mode_distribution"] == {}
        assert stats["avg_messages_per_session"] == 0
        assert stats["avg_queries_with_links"] == 0

    def test_stats_after_sessions(self, populated_db):
        """После нескольких save_exchange → метрики корректны."""
        stats = get_stats()

        assert stats["total_sessions"] == 3
        assert stats["total_queries"] == 5
        assert stats["mode_distribution"]["search"] == 3
        assert stats["mode_distribution"]["consultation"] == 1
        assert stats["mode_distribution"]["off_topic"] == 1
        # 5 запросов / 3 сессии = 1.67
        assert abs(stats["avg_messages_per_session"] - 1.67) < 0.01

    def test_mode_distribution_separate(self, clean_db):
        """mode_distribution считает search и consultation отдельно."""
        db_path = clean_db
        conn = sqlite3.connect(db_path)

        # 3 search, 2 consultation в одной сессии
        conn.execute("INSERT INTO sessions (title) VALUES (?)", ("Test",))
        for i in range(3):
            conn.execute(
                "INSERT INTO chat_history (session_id, user_query, mode) VALUES (?, ?, ?)",
                (1, f"search {i}", "search"),
            )
        for i in range(2):
            conn.execute(
                "INSERT INTO chat_history (session_id, user_query, mode) VALUES (?, ?, ?)",
                (1, f"consult {i}", "consultation"),
            )
        conn.commit()
        conn.close()

        stats = get_stats()

        assert stats["mode_distribution"]["search"] == 3
        assert stats["mode_distribution"]["consultation"] == 2
        assert len(stats["mode_distribution"]) == 2

    def test_single_session_single_search(self, clean_db):
        """Одна сессия, один search-запрос."""
        db_path = clean_db
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO sessions (title) VALUES (?)", ("Single",))
        conn.execute(
            "INSERT INTO chat_history (session_id, user_query, mode) VALUES (?, ?, ?)",
            (1, "Fender Strat", "search"),
        )
        conn.commit()
        conn.close()

        stats = get_stats()

        assert stats["total_sessions"] == 1
        assert stats["total_queries"] == 1
        assert stats["mode_distribution"] == {"search": 1}
        assert stats["avg_messages_per_session"] == 1.0

    def test_consultation_only_no_search_links(self, clean_db):
        """Только consultation — avg_queries_with_links = 0."""
        db_path = clean_db
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO sessions (title) VALUES (?)", ("Consult only",))
        conn.execute(
            "INSERT INTO chat_history (session_id, user_query, mode) VALUES (?, ?, ?)",
            (1, "Как играть?", "consultation"),
        )
        conn.commit()
        conn.close()

        stats = get_stats()

        assert stats["total_sessions"] == 1
        assert stats["total_queries"] == 1
        assert stats["mode_distribution"] == {"consultation": 1}
        assert stats["avg_queries_with_links"] == 0
