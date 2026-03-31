"""Тесты API-контракта между backend и frontend."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Создаёт тестовый клиент."""
    return TestClient(app)


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
        with client.websocket_connect("/chat") as websocket:
            # Получаем начальное сообщение
            websocket.receive_json()

            # Отправляем search-запрос
            websocket.send_json({"query": "Fender Stratocaster купить"})

            # Получаем result
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert "results" in result_data
            assert len(result_data["results"]) > 0

            # Проверяем что поля в camelCase
            first_result = result_data["results"][0]
            assert "imageUrl" in first_result, "Должно быть поле imageUrl (camelCase)"
            assert "listingUrl" in first_result, "Должно быть поле listingUrl (camelCase)"

            # Проверяем что НЕТ полей в snake_case
            assert "image_url" not in first_result, "Не должно быть поля image_url (snake_case)"
            assert "listing_url" not in first_result, "Не должно быть поля listing_url (snake_case)"

    def test_search_result_has_required_fields(self, client):
        """Search-результат содержит все обязательные поля: id, title, price, listingUrl."""
        with client.websocket_connect("/chat") as websocket:
            # Получаем начальное сообщение
            websocket.receive_json()

            # Отправляем search-запрос
            websocket.send_json({"query": "гитара Fender"})

            # Получаем result
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert "results" in result_data
            assert len(result_data["results"]) > 0

            first_result = result_data["results"][0]

            # Проверяем обязательные поля
            assert "id" in first_result, "Должно быть поле id"
            assert "title" in first_result, "Должно быть поле title"
            assert "price" in first_result, "Должно быть поле price"
            assert "listingUrl" in first_result, "Должно быть поле listingUrl"

    def test_search_result_no_score_field(self, client):
        """Search-результат НЕ содержит поле score."""
        with client.websocket_connect("/chat") as websocket:
            # Получаем начальное сообщение
            websocket.receive_json()

            # Отправляем search-запрос
            websocket.send_json({"query": "купить гитару"})

            # Получаем result
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "search"
            assert "results" in result_data
            assert len(result_data["results"]) > 0

            # Проверяем что score НЕ присутствует в результатах
            for result in result_data["results"]:
                assert "score" not in result, "Поле score не должно присутствовать в результатах"


class TestConsultationModeContract:
    """Тесты контракта для consultation-режима."""

    def test_consultation_result_has_answer_field(self, client):
        """Consultation-результат содержит поле answer (не reply)."""
        with client.websocket_connect("/chat") as websocket:
            # Получаем начальное сообщение
            websocket.receive_json()

            # Отправляем consultation-запрос
            websocket.send_json({"query": "Как настроить гитару?"})

            # Получаем result
            result_data = receive_until_type(websocket, "result")

            assert result_data["mode"] == "consultation"

            # Проверяем что есть поле answer
            assert "answer" in result_data, "Должно быть поле answer"
            assert isinstance(result_data["answer"], str)
            assert len(result_data["answer"]) > 0

            # Проверяем что НЕТ поля reply
            assert "reply" not in result_data, "Не должно быть поля reply"


class TestGeneralContract:
    """Общие тесты API-контракта."""

    def test_result_has_mode_field(self, client):
        """Любой result содержит поле mode."""
        with client.websocket_connect("/chat") as websocket:
            # Получаем начальное сообщение
            websocket.receive_json()

            # Отправляем запрос
            websocket.send_json({"query": "гитара"})

            # Получаем result
            result_data = receive_until_type(websocket, "result")

            assert "mode" in result_data
            assert result_data["mode"] in ["search", "consultation"]

    def test_status_messages_sent_before_result(self, client):
        """Перед result отправляются status-сообщения."""
        with client.websocket_connect("/chat") as websocket:
            # Получаем начальное сообщение
            first_message = websocket.receive_json()
            assert first_message["type"] == "status"

            # Отправляем запрос
            websocket.send_json({"query": "Fender Stratocaster"})

            # Получаем как минимум одно status перед result
            status_received = False
            while True:
                data = websocket.receive_json()
                if data.get("type") == "status":
                    status_received = True
                    assert "status" in data
                elif data.get("type") == "result":
                    break

            assert status_received, "Должно быть хотя бы одно status-сообщение перед result"
