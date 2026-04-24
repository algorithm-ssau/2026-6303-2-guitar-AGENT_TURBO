"""E2E-тесты истории через REST и WebSocket."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def history_client(tmp_path, monkeypatch):
    """TestClient с чистой БД истории."""
    db_path = str(tmp_path / "history_e2e.db")
    monkeypatch.setenv("CHAT_DB_PATH", db_path)
    monkeypatch.setenv("USE_MOCK_REVERB", "true")

    import backend.history.service as history_service

    if history_service._connection is not None:
        history_service._connection.close()
    history_service._DB_PATH = db_path
    history_service._connection = None

    from backend.main import app

    with TestClient(app) as client:
        yield client

    if history_service._connection is not None:
        history_service._connection.close()
    history_service._connection = None


def _receive_result(websocket):
    while True:
        data = websocket.receive_json()
        if data["type"] == "result":
            return data
        if data["type"] == "error":
            pytest.fail(f"Получена ошибка WebSocket: {data}")


def test_history_rest_and_websocket_flow(history_client):
    first_query = "Как выбрать гитару для джаза?"
    second_query = "Чем P90 отличаются от хамбакеров?"

    create_response = history_client.post("/api/sessions", json={"title": first_query})
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]

    def fake_interpret_query(query, on_status=None, session_id=None):
        if on_status:
            on_status("Формирую ответ...")
        return {
            "mode": "consultation",
            "answer": f"Ответ на запрос: {query}",
        }

    with patch("backend.main.interpret_query", side_effect=fake_interpret_query):
        with history_client.websocket_connect("/chat") as websocket:
            websocket.send_json({"query": first_query, "sessionId": session_id})
            first_result = _receive_result(websocket)
            assert first_result["mode"] == "consultation"

            websocket.send_json({"query": second_query, "sessionId": session_id})
            second_result = _receive_result(websocket)
            assert second_result["mode"] == "consultation"

    sessions_response = history_client.get("/api/sessions")
    assert sessions_response.status_code == 200
    sessions = sessions_response.json()["sessions"]
    assert any(item["id"] == session_id and item["title"] == first_query for item in sessions)

    messages_response = history_client.get(f"/api/sessions/{session_id}/messages")
    assert messages_response.status_code == 200
    messages = messages_response.json()["items"]
    assert len(messages) == 2
    assert [item["userQuery"] for item in messages] == [first_query, second_query]

    delete_response = history_client.delete(f"/api/sessions/{session_id}")
    assert delete_response.status_code == 200

    sessions_after_delete = history_client.get("/api/sessions").json()["sessions"]
    assert all(item["id"] != session_id for item in sessions_after_delete)

    extra_response = history_client.post("/api/sessions", json={"title": "Временная сессия"})
    assert extra_response.status_code == 200

    clear_response = history_client.delete("/api/history")
    assert clear_response.status_code == 200

    final_sessions = history_client.get("/api/sessions").json()["sessions"]
    assert final_sessions == []
