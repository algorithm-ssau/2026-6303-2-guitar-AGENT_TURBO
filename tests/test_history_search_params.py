import importlib


def test_history_saves_and_reads_search_params(tmp_path, monkeypatch):
    import backend.history.service as history_service

    monkeypatch.setenv("CHAT_DB_PATH", str(tmp_path / "chat.db"))
    history_service._connection = None
    history_service._DB_PATH = str(tmp_path / "chat.db")
    importlib.reload(history_service)

    history_service.init_db()
    session_id = history_service.create_session("Telecaster")
    search_params = {
        "searchQueries": ["Fender Telecaster"],
        "priceMax": 800,
        "type": "telecaster",
    }

    history_service.save_exchange(
        session_id=session_id,
        user_query="Подбери Telecaster до 800$",
        mode="search",
        results=[],
        search_params=search_params,
    )

    items = history_service.get_session_messages(session_id)

    assert items[0]["search_params"] == search_params


def test_history_old_entries_return_null_search_params(tmp_path, monkeypatch):
    import backend.history.service as history_service

    monkeypatch.setenv("CHAT_DB_PATH", str(tmp_path / "chat.db"))
    history_service._connection = None
    history_service._DB_PATH = str(tmp_path / "chat.db")
    importlib.reload(history_service)

    history_service.init_db()
    session_id = history_service.create_session("Old")
    history_service.save_exchange(session_id, "Что такое хамбакер?", "consultation", answer="Ответ")

    items = history_service.get_session_messages(session_id)

    assert items[0]["search_params"] is None
