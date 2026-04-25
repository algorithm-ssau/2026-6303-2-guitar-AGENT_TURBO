import pytest
from fastapi.testclient import TestClient
from backend.main import app 

client = TestClient(app)

def test_feedback_flow():
    # 1. Отправляем позитивный отзыв (up)
    response = client.post("/api/feedback/", json={
        "session_id": 999,
        "guitar_id": "test_fender",
        "rating": "up",
        "query": "stratocaster"
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data

    # 2. Проверяем, что статистика обновилась
    stats = client.get("/api/feedback/stats").json()
    assert stats["total"] >= 1
    assert stats["up"] >= 1
    # Проверяем, что наша гитара появилась в статистике
    assert "test_fender" in stats["by_guitar"]
    assert stats["by_guitar"]["test_fender"]["up"] == 1

def test_invalid_rating():
    # 3. Пытаемся отправить некорректный рейтинг ("mid" вместо "up"/"down")
    response = client.post("/api/feedback/", json={
        "session_id": 999,
        "guitar_id": "test_guitar",
        "rating": "mid"  # Невалидное значение
    })
    assert response.status_code == 422

def test_stats_structure():
    stats = client.get("/api/feedback/stats").json()
    assert "total" in stats
    assert "up" in stats
    assert "down" in stats
    assert "ratio" in stats
    assert "by_guitar" in stats
    assert isinstance(stats["by_guitar"], dict)