"""
Интеграционные тесты для WebSocket + useChat
Проверка полного flow через FastAPI TestClient.
"""
import os
import pytest
from fastapi.testclient import TestClient

# Устанавливаем переменную окружения для использования мока Reverb
os.environ["USE_MOCK_REVERB"] = "true"

from backend.main import app

client = TestClient(app)


@pytest.mark.websocket
def test_search_query_flow():
    """
    Search query → серия status → result с mode="search" и непустыми results.
    """
    with client.websocket_connect("/chat") as websocket:
        # Отправляем search query
        websocket.send_json({"query": "хочу гитару за $500"})

        # Получаем сообщения
        statuses = []
        result = None

        while True:
            data = websocket.receive_json()
            if data["type"] == "status":
                statuses.append(data)
            elif data["type"] == "result":
                result = data
                break
            elif data["type"] == "error":
                pytest.fail(f"Получена ошибка: {data}")

        # Проверяем что были статусы
        assert len(statuses) >= 1, "Должны быть статусы"

        # Проверяем результат
        assert result is not None, "Результат должен быть"
        assert result["mode"] == "search", "Режим должен быть search"
        assert "results" in result, "Должен быть ключ results"


@pytest.mark.websocket
def test_consultation_query_flow():
    """
    Consultation query → status → result с mode="consultation" и непустым answer.
    """
    with client.websocket_connect("/chat") as websocket:
        # Отправляем consultation query
        websocket.send_json({"query": "Как настроить гитару?"})

        statuses = []
        result = None

        while True:
            data = websocket.receive_json()
            if data["type"] == "status":
                statuses.append(data)
            elif data["type"] == "result":
                result = data
                break
            elif data["type"] == "error":
                pytest.fail(f"Получена ошибка: {data}")

        # Проверяем результат
        assert result is not None, "Результат должен быть"
        assert result["mode"] == "consultation", "Режим должен быть consultation"
        assert "answer" in result, "Должен быть ключ answer"
        assert len(result["answer"]) > 0, "Ответ не должен быть пустым"


@pytest.mark.websocket
def test_sequential_requests():
    """
    Два последовательных запроса в одном WS-соединении → оба работают.
    """
    with client.websocket_connect("/chat") as websocket:
        # Первый запрос
        websocket.send_json({"query": "хочу гитару"})

        result1 = None
        while True:
            data = websocket.receive_json()
            if data["type"] == "result":
                result1 = data
                break
            elif data["type"] == "error":
                pytest.fail(f"Получена ошибка при первом запросе: {data}")

        assert result1 is not None, "Первый результат должен быть"

        # Второй запрос в том же соединении
        websocket.send_json({"query": "какой бюджет?"})

        result2 = None
        while True:
            data = websocket.receive_json()
            if data["type"] == "result":
                result2 = data
                break
            elif data["type"] == "error":
                pytest.fail(f"Получена ошибка при втором запросе: {data}")

        assert result2 is not None, "Второй результат должен быть"


@pytest.mark.websocket
def test_result_format():
    """
    Проверка формата результатов: каждый result содержит id, title, price, listing_url.
    """
    with client.websocket_connect("/chat") as websocket:
        websocket.send_json({"query": "гитара за $1000"})

        result = None
        while True:
            data = websocket.receive_json()
            if data["type"] == "result":
                result = data
                break
            elif data["type"] == "error":
                pytest.fail(f"Получена ошибка: {data}")

        assert result is not None, "Результат должен быть"
        assert result["mode"] == "search", "Режим должен быть search"

        # Проверяем что results не пустой
        assert len(result["results"]) > 0, "Результаты не должны быть пустыми"

        # Проверяем формат каждого результата
        for item in result["results"]:
            # Должен быть id или title
            assert "id" in item or "title" in item, "Должен быть id или title"
            # Должен быть title
            assert "title" in item, "Должен быть title"
            # Должна быть price
            assert "price" in item, "Должна быть price"
            # Должен быть listing_url (в camelCase)
            assert "listingUrl" in item, "Должен быть listingUrl (camelCase)"


@pytest.mark.websocket
def test_empty_query_error():
    """
    Пустой запрос → type="error".
    """
    with client.websocket_connect("/chat") as websocket:
        # Отправляем пустой запрос
        websocket.send_json({"query": ""})

        data = websocket.receive_json()

        assert data["type"] == "error", "Должна быть ошибка"
        assert "status" in data, "Должен быть ключ status"


@pytest.mark.websocket
def test_status_updates_order():
    """
    Проверяем что статусы приходят в правильном порядке до result.
    """
    with client.websocket_connect("/chat") as websocket:
        websocket.send_json({"query": "хочу гитару"})

        statuses = []
        result = None

        while True:
            data = websocket.receive_json()
            if data["type"] == "status":
                statuses.append(data["status"])
            elif data["type"] == "result":
                result = data
                break

        # Проверяем что статусы были до result
        assert len(statuses) > 0, "Должны быть статусы"
        # Первый статус должен быть "Определяю режим..."
        assert statuses[0] == "Определяю режим...", "Первый статус должен быть 'Определяю режим...'"
