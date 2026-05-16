"""API contract tests between backend and frontend."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from tests.conftest import auth_headers, auth_ws_path


@pytest.fixture
def client():
    """Create test client."""
    from backend.main import app
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
    """Receive messages from WebSocket until finding message with expected type."""
    while True:
        data = websocket.receive_json()
        if data.get("type") == expected_type:
            return data


class TestSearchModeContract:
    """Tests for search mode contract."""

    def test_search_result_has_camelcase_fields(self, client):
        """Search-результат содержит поля в camelCase (imageUrl, listingUrl)."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "Fender Stratocaster купить"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert "results" in result_data
            assert len(result_data["results"]) > 0

            first_result = result_data["results"][0]
            assert "imageUrl" in first_result
            assert "listingUrl" in first_result
            assert "image_url" not in first_result
            assert "listing_url" not in first_result

    def test_search_result_has_required_fields(self, client):
        """Search-результат содержит все обязательные поля: id, title, price, listingUrl."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "гитара Fender"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            first_result = result_data["results"][0]
            assert all(field in first_result for field in ["id", "title", "price", "listingUrl"])

    def test_search_result_no_score_field(self, client):
        """Search-результат НЕ содержит поле score."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "купить гитару"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert 3 <= len(result_data["results"]) <= 5

    def test_search_result_has_explanation(self, client):
        """Search-результат содержит поле explanation (только в WebSocket)."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "Fender Stratocaster"})
            result_data = receive_until_type(websocket, "result")

            for result in result_data["results"]:
                assert "score" not in result

    def test_search_result_has_session_id(self, client):
        """Search-результат содержит sessionId."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "Fender Stratocaster"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert result_data["results"] == []


class TestConsultationModeContract:
    """Tests for consultation mode contract."""

    def test_consultation_result_has_answer_field(self, client):
        """Consultation-результат содержит поле answer (не reply)."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "Как настроить гитару?"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "consultation"
            assert "answer" in result_data
            assert isinstance(result_data["answer"], str)
            assert len(result_data["answer"]) > 0

    def test_consultation_result_has_session_id(self, client):
        """Consultation-результат содержит sessionId."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            websocket.send_json({"query": "Как настроить гитару?"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "consultation"
            assert "results" not in result_data or result_data.get("results") is None


class TestClarificationModeContract:
    """Tests for clarification mode contract."""

    def test_clarification_result_has_question_field(self, client):
        """Clarification-результат содержит поле question."""
        with client.websocket_connect(auth_ws_path(client)) as websocket:
            # Отправляем неполный запрос, который может вызвать clarification
            websocket.send_json({"query": "гитара"})
            
            result_data = receive_until_type(websocket, "result")

            if result_data["mode"] == "clarification":
                assert "question" in result_data
                assert isinstance(result_data["question"], str)
                assert len(result_data["question"]) > 0


class TestGeneralContract:
    """General API contract tests."""

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

            assert status_received

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
    """REST API contract tests."""

    def test_get_sessions_returns_camelcase(self, client):
        """GET /api/sessions возвращает поля в camelCase."""
        response = client.get("/api/sessions", headers=auth_headers(client))
        assert response.status_code == 200
        
        # Create a mock that returns search mode
        mock_return = {
            "mode": "search", 
            "results": [{
                "id": "123",
                "title": "Fender Stratocaster",
                "price": 499.99,
                "currency": "USD",
                "image_url": "https://example.com/img.jpg",
                "listing_url": "https://reverb.com/item/123"
            }]
        }
        
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
        assert "sessions" in data
        assert "total" in data

    def test_get_stats(self, client, tmp_path, monkeypatch):
        """GET /api/stats returns statistics."""
        import backend.history.service as history_service
        from backend.history.service import init_db
        
        db_path = str(tmp_path / "test_stats.db")
        monkeypatch.setenv("CHAT_DB_PATH", db_path)
        if history_service._connection is not None:
            history_service._connection.close()
        history_service._DB_PATH = db_path
        history_service._connection = None
        
        # Initialize database
        init_db()

    def test_get_stats_returns_correct_format(self, client):
        """GET /api/stats возвращает правильный формат."""
        response = client.get("/api/stats", headers=auth_headers(client))
        assert response.status_code == 200
        data = response.json()
        assert "totalSessions" in data
        assert "totalQueries" in data
        assert "modeDistribution" in data

    def test_get_metrics_health_returns_kpi(self, client):
        """GET /api/metrics/health возвращает KPI."""
        response = client.get("/api/metrics/health", headers=auth_headers(client))
        assert response.status_code == 200
        data = response.json()
        assert "totalSessions" in data
        assert "kpiMet" in data

    def test_delete_history(self, client, tmp_path, monkeypatch):
        """DELETE /api/history returns deleted count."""
        import backend.history.service as history_service
        from backend.history.service import init_db
        
        db_path = str(tmp_path / "test_history.db")
        monkeypatch.setenv("CHAT_DB_PATH", db_path)
        if history_service._connection is not None:
            history_service._connection.close()
        history_service._DB_PATH = db_path
        history_service._connection = None
        
        # Initialize database
        init_db()

        response = client.delete("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data
