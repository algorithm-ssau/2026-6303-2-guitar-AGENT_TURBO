import pytest
from fastapi.testclient import TestClient
from backend.main import app 
from backend.feedback.service import init_feedback_table
from tests.conftest import auth_headers

client = TestClient(app)

def test_feedback_flow():
    init_feedback_table()
    headers = auth_headers(client)
    session_response = client.post("/api/sessions", json={"title": "Feedback test"}, headers=headers)
    assert session_response.status_code == 200
    session_id = session_response.json()["id"]
    guitar_id = f"test_fender_{session_id}"

    # 1. Отправляем позитивный отзыв (up)
    response = client.post("/api/feedback/", json={
        "session_id": session_id,
        "guitar_id": guitar_id,
        "rating": "up",
        "query": "stratocaster"
    }, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data

    # 2. Проверяем, что статистика обновилась
    stats = client.get("/api/feedback/stats", headers=headers).json()
    assert stats["total"] >= 1
    assert stats["up"] >= 1
    # Проверяем, что наша гитара появилась в статистике
    assert guitar_id in stats["by_guitar"]
    assert stats["by_guitar"][guitar_id]["up"] == 1

def test_invalid_rating():
    init_feedback_table()
    headers = auth_headers(client)
    # 3. Пытаемся отправить некорректный рейтинг ("mid" вместо "up"/"down")
    response = client.post("/api/feedback/", json={
        "session_id": 999,
        "guitar_id": "test_guitar",
        "rating": "mid"  # Невалидное значение
    }, headers=headers)
    assert response.status_code == 422

def test_stats_structure():
    init_feedback_table()
    stats = client.get("/api/feedback/stats", headers=auth_headers(client)).json()
    assert "total" in stats
    assert "up" in stats
    assert "down" in stats
    assert "ratio" in stats
    assert "by_guitar" in stats
    assert isinstance(stats["by_guitar"], dict)
