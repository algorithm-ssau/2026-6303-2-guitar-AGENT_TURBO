"""API contract tests between backend and frontend."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    """Create test client."""
    from backend.main import app
    return TestClient(app)


def receive_until_type(websocket, expected_type: str):
    """Receive messages from WebSocket until finding message with expected type."""
    while True:
        data = websocket.receive_json()
        if data.get("type") == expected_type:
            return data


class TestSearchModeContract:
    """Tests for search mode contract."""

    def test_search_result_has_camelcase_fields(self, client):
        """Search result contains camelCase fields (imageUrl, listingUrl)."""
        with client.websocket_connect("/chat") as websocket:
            websocket.receive_json()
            websocket.send_json({"query": "Fender Stratocaster"})
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
        """Search result contains required fields."""
        with client.websocket_connect("/chat") as websocket:
            websocket.receive_json()
            websocket.send_json({"query": "Fender guitar"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            first_result = result_data["results"][0]
            assert all(field in first_result for field in ["id", "title", "price", "listingUrl"])

    def test_search_result_3_to_5_results(self, client):
        """Search result contains 3-5 results."""
        with client.websocket_connect("/chat") as websocket:
            websocket.receive_json()
            websocket.send_json({"query": "Fender Stratocaster"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert 3 <= len(result_data["results"]) <= 5

    def test_search_result_no_score_field(self, client):
        """Search result does NOT contain score field."""
        with client.websocket_connect("/chat") as websocket:
            websocket.receive_json()
            websocket.send_json({"query": "buy guitar"})
            result_data = receive_until_type(websocket, "result")

            for result in result_data["results"]:
                assert "score" not in result

    def test_search_empty_results(self, client):
        """Search with non-existent query returns empty results."""
        with client.websocket_connect("/chat") as websocket:
            websocket.receive_json()
            websocket.send_json({"query": "asdfghjklqwertyuiop123456"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert result_data["results"] == []


class TestConsultationModeContract:
    """Tests for consultation mode contract."""

    def test_consultation_result_has_answer_field(self, client):
        """Consultation result contains answer field."""
        with client.websocket_connect("/chat") as websocket:
            websocket.receive_json()
            websocket.send_json({"query": "How to tune a guitar?"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "consultation"
            assert "answer" in result_data
            assert isinstance(result_data["answer"], str)
            assert len(result_data["answer"]) > 0

    def test_consultation_no_results_field(self, client):
        """Consultation result does NOT contain results field."""
        with client.websocket_connect("/chat") as websocket:
            websocket.receive_json()
            websocket.send_json({"query": "What is the difference between Les Paul and SG?"})
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "consultation"
            assert "results" not in result_data or result_data.get("results") is None


class TestClarificationModeContract:
    """Tests for clarification mode contract."""

    def test_clarification_result_has_question_field(self, client):
        """Clarification result contains question field."""
        with client.websocket_connect("/chat") as websocket:
            websocket.receive_json()
            websocket.send_json({"query": "guitar"})
            result_data = receive_until_type(websocket, "result")

            if result_data["mode"] == "clarification":
                assert "question" in result_data
                assert isinstance(result_data["question"], str)
                assert len(result_data["question"]) > 0


class TestGeneralContract:
    """General API contract tests."""

    def test_result_has_mode_field(self, client):
        """Any result contains mode field."""
        with client.websocket_connect("/chat") as websocket:
            websocket.receive_json()
            websocket.send_json({"query": "guitar"})
            result_data = receive_until_type(websocket, "result")

            assert "mode" in result_data
            assert result_data["mode"] in ["search", "consultation", "clarification"]

    def test_status_messages_sent_before_result(self, client):
        """Status messages are sent before result."""
        with client.websocket_connect("/chat") as websocket:
            first_message = websocket.receive_json()
            assert first_message["type"] == "status"

            websocket.send_json({"query": "Fender Stratocaster"})

            status_received = False
            while True:
                data = websocket.receive_json()
                if data.get("type") == "status":
                    status_received = True
                    assert "status" in data
                elif data.get("type") == "result":
                    break

            assert status_received

    def test_ws_error_on_empty_query(self, client):
        """WebSocket returns error on empty query."""
        with client.websocket_connect("/chat") as websocket:
            websocket.receive_json()
            websocket.send_json({"query": ""})
            
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "status" in data

    def test_ws_error_on_missing_query(self, client):
        """WebSocket returns error if query is missing."""
        with client.websocket_connect("/chat") as websocket:
            websocket.receive_json()
            websocket.send_json({})
            
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "status" in data


class TestRESTContract:
    """REST API contract tests."""

    def test_post_chat_search_mode(self, client):
        """POST /api/chat returns search result."""
        from unittest.mock import MagicMock
        
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
        
        with patch("backend.search.router.interpret_query", return_value=mock_return):
            response = client.post("/api/chat", json={"query": "Fender Stratocaster"})
            assert response.status_code == 200
            data = response.json()
            assert data["mode"] == "search"
            assert "results" in data

    def test_post_chat_consultation_mode(self, client):
        """POST /api/chat returns consultation result."""
        mock_return = {"mode": "consultation", "answer": "This is a consultation answer."}
        
        with patch("backend.search.router.interpret_query", return_value=mock_return):
            response = client.post("/api/chat", json={"query": "How to tune a guitar?"})
            assert response.status_code == 200
            data = response.json()
            assert data["mode"] == "consultation"
            assert "answer" in data

    def test_post_chat_clarification_mode(self, client):
        """POST /api/chat returns clarification result."""
        mock_return = {"mode": "clarification", "question": "What is your budget?"}
        
        with patch("backend.search.router.interpret_query", return_value=mock_return):
            response = client.post("/api/chat", json={"query": "guitar"})
            assert response.status_code == 200
            data = response.json()
            assert data["mode"] == "clarification"
            assert "question" in data

    def test_post_chat_validation_error_empty(self, client):
        """POST /api/chat returns 422 on empty query."""
        response = client.post("/api/chat", json={"query": ""})
        assert response.status_code == 422

    def test_post_chat_validation_error_short(self, client):
        """POST /api/chat returns 422 on short query."""
        response = client.post("/api/chat", json={"query": "a"})
        assert response.status_code == 422

    def test_get_sessions(self, client, tmp_path, monkeypatch):
        """GET /api/sessions returns session list."""
        import backend.history.service as history_service
        from backend.history.service import init_db
        
        db_path = str(tmp_path / "test_sessions.db")
        monkeypatch.setenv("CHAT_DB_PATH", db_path)
        if history_service._connection is not None:
            history_service._connection.close()
        history_service._DB_PATH = db_path
        history_service._connection = None
        
        # Initialize database
        init_db()

        response = client.get("/api/sessions")
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

        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "totalSessions" in data
        assert "totalQueries" in data
        assert "modeDistribution" in data

    def test_get_metrics_health(self, client, tmp_path, monkeypatch):
        """GET /api/metrics/health returns metrics."""
        import backend.history.service as history_service
        
        db_path = str(tmp_path / "test_metrics.db")
        monkeypatch.setenv("CHAT_DB_PATH", db_path)
        if history_service._connection is not None:
            history_service._connection.close()
        history_service._DB_PATH = db_path
        history_service._connection = None

        from backend.analytics.pipeline_metrics import init_metrics_table
        init_metrics_table()

        response = client.get("/api/metrics/health")
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
