"""Тесты API-контракта между backend и frontend."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from tests.conftest import auth_headers, auth_ws_path


@pytest.fixture
def client():
    """Создаёт тестовый клиент."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_agent(monkeypatch):
    def fake_interpret_query(query, on_status=None, session_id=None):
        if on_status:
            on_status("Формирую ответ...")
        if "настро" in query:
            return {"mode": "consultation", "answer": f"Ответ на запрос: {query}"}
        if query.strip() == "гитара":
            return {"mode": "clarification", "question": "Какой бюджет?"}
        return {
            "mode": "search",
            "results": [{
                "id": "test-1",
                "title": "Fender Stratocaster",
                "price": 500,
                "currency": "USD",
                "image_url": "https://example.com/image.jpg",
                "listing_url": "https://example.com/listing",
            }],
        }

    monkeypatch.setattr("backend.main.interpret_query", fake_interpret_query)
    monkeypatch.setattr("backend.agent.service.create_llm_client", lambda: None)
    monkeypatch.setattr("backend.agent.explanation.generate_explanation", lambda *args, **kwargs: "Тестовое объяснение")


def receive_until_type(websocket, expected_type: str):
    """Получает сообщения из WebSocket до тех пор, пока не найдёт сообщение с нужным типом."""
    while True:
        data = websocket.receive_json()
        if data.get("type") == expected_type:
            return data


class TestSearchModeContract:
    """Тесты контракта для search-режима."""

    def test_search_result_has_camelcase_fields(self, client):
        """Search-результат содержит поля в camelCase (imageUrl, listingUrl)."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "Fender Stratocaster купить"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert "results" in result_data
            assert len(result_data["results"]) > 0

            first_result = result_data["results"][0]
            assert "imageUrl" in first_result, "Должно быть поле imageUrl (camelCase)"
            assert "listingUrl" in first_result, "Должно быть поле listingUrl (camelCase)"
            assert "image_url" not in first_result, "Не должно быть поля image_url (snake_case)"
            assert "listing_url" not in first_result, "Не должно быть поля listing_url (snake_case)"

    def test_search_result_has_required_fields(self, client):
        """Search-результат содержит все обязательные поля: id, title, price, listingUrl."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "гитара Fender"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert "results" in result_data
            assert len(result_data["results"]) > 0

            first_result = result_data["results"][0]
            assert "id" in first_result, "Должно быть поле id"
            assert "title" in first_result, "Должно быть поле title"
            assert "price" in first_result, "Должно быть поле price"
            assert "listingUrl" in first_result, "Должно быть поле listingUrl"

    def test_search_result_no_score_field(self, client):
        """Search-результат НЕ содержит поле score."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "купить гитару"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert "results" in result_data
            assert len(result_data["results"]) > 0

            for result in result_data["results"]:
                assert "score" not in result, "Поле score не должно присутствовать в результатах"

    def test_search_result_has_explanation(self, client):
        """Search-результат содержит поле explanation (только в WebSocket)."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "Fender Stratocaster"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert "explanation" in result_data, "Должно быть поле explanation"
            assert isinstance(result_data["explanation"], str)
            assert len(result_data["explanation"]) > 0

    def test_search_result_has_session_id(self, client):
        """Search-результат содержит sessionId."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "Fender Stratocaster"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert "sessionId" in result_data, "Должно быть поле sessionId"
            assert isinstance(result_data["sessionId"], int)


class TestConsultationModeContract:
    """Тесты контракта для consultation-режима."""

    def test_consultation_result_has_answer_field(self, client):
        """Consultation-результат содержит поле answer (не reply)."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "Как настроить гитару?"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "consultation"
            assert "answer" in result_data, "Должно быть поле answer"
            assert isinstance(result_data["answer"], str)
            assert len(result_data["answer"]) > 0
            assert "reply" not in result_data, "Не должно быть поля reply"

    def test_consultation_result_has_session_id(self, client):
        """Consultation-результат содержит sessionId."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "Как настроить гитару?"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "consultation"
            assert "sessionId" in result_data, "Должно быть поле sessionId"
            assert isinstance(result_data["sessionId"], int)


class TestClarificationModeContract:
    """Тесты контракта для clarification-режима."""

    def test_clarification_result_has_question_field(self, client):
        """Clarification-результат содержит поле question."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            # Отправляем неполный запрос, который может вызвать clarification
            websocket.send_json({"query": "гитара"})
            
            result_data = receive_until_type(websocket, "result")
            
            # Проверяем что ответ либо search, либо consultation, либо clarification
            assert result_data["mode"] in ["search", "consultation", "clarification"]
            if result_data["mode"] == "clarification":
                assert "question" in result_data, "Должно быть поле question"
                assert isinstance(result_data["question"], str)


class TestGeneralContract:
    """Общие тесты API-контракта."""

    def test_result_has_mode_field(self, client):
        """Любой result содержит поле mode."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "гитара"})
            result_data = receive_until_type(websocket, "result")

            assert "mode" in result_data
            assert result_data["mode"] in ["search", "consultation", "clarification"]

    def test_status_messages_sent_before_result(self, client):
        """Перед result отправляются status-сообщения."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "Fender Stratocaster"})
            first_message = websocket.receive_json()
            assert first_message["type"] == "status"

            status_received = False
            while True:
                data = websocket.receive_json()
                if data.get("type") == "status":
                    status_received = True
                    assert "status" in data
                elif data.get("type") == "result":
                    break

            assert status_received, "Должно быть хотя бы одно status-сообщение перед result"

    def test_empty_query_returns_error(self, client):
        """Пустой запрос возвращает ошибку."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            # Пустой запрос
            websocket.send_json({"query": ""})
            data = receive_until_type(websocket, "error")
            assert data["type"] == "error"
            assert "status" in data

    def test_websocket_error_has_correct_format(self, client):
        """WebSocket ошибка имеет правильный формат."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": ""})
            error_data = receive_until_type(websocket, "error")
            
            assert error_data["type"] == "error"
            assert "status" in error_data
            assert isinstance(error_data["status"], str)


class TestRESTContract:
    """Тесты REST API контракта."""

    def test_get_sessions_returns_camelcase(self, client):
        """GET /api/sessions возвращает поля в camelCase."""
        response = client.get("/api/sessions", headers=auth_headers(client))
        assert response.status_code == 200
        
        data = response.json()
        assert "sessions" in data
        assert "total" in data
        
        if len(data["sessions"]) > 0:
            session = data["sessions"][0]
            assert "createdAt" in session, "Должно быть поле createdAt (camelCase)"
            assert "updatedAt" in session, "Должно быть поле updatedAt (camelCase)"
            assert "created_at" not in session, "Не должно быть поля created_at (snake_case)"

    def test_create_session_returns_id(self, client):
        """POST /api/sessions возвращает id."""
        response = client.post("/api/sessions", json={"title": "Test Session"}, headers=auth_headers(client))
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert isinstance(data["id"], int)

    def test_delete_session_returns_ok(self, client):
        """DELETE /api/sessions/{id} возвращает ok."""
        headers = auth_headers(client)
        create_response = client.post("/api/sessions", json={"title": "To Delete"}, headers=headers)
        session_id = create_response.json()["id"]
        
        delete_response = client.delete(f"/api/sessions/{session_id}", headers=headers)
        assert delete_response.status_code == 200
        assert delete_response.json() == {"ok": True}

    def test_clear_history_returns_deleted_count(self, client):
        """DELETE /api/history возвращает deleted count."""
        response = client.delete("/api/history", headers=auth_headers(client))
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data
        assert isinstance(data["deleted"], int)

    def test_get_stats_returns_correct_format(self, client):
        """GET /api/stats возвращает правильный формат."""
        response = client.get("/api/stats", headers=auth_headers(client))
        assert response.status_code == 200
        
        data = response.json()
        assert "totalSessions" in data
        assert "totalQueries" in data
        assert "modeDistribution" in data
        assert "avgMessagesPerSession" in data

    def test_get_metrics_health_returns_kpi(self, client):
        """GET /api/metrics/health возвращает KPI."""
        response = client.get("/api/metrics/health", headers=auth_headers(client))
        assert response.status_code == 200
        
        data = response.json()
        assert "totalSessions" in data
        assert "kpiMet" in data

    def test_parse_query_endpoint_is_removed(self, client):
        """POST /api/query/parse больше не существует."""
        response = client.post("/api/query/parse", json={"query": "Fender до 1000$"})
        assert response.status_code == 404
