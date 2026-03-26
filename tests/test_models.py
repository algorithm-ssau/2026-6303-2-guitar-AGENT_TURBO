import pytest
from pydantic import ValidationError

from backend.search.models import ChatRequest, ChatResponse, SearchResult


class TestChatRequest:
    """Тесты для модели ChatRequest."""

    def test_valid_request(self):
        """Валидный запрос с query."""
        request = ChatRequest(query="Нужна гитара для металла до 45 тысяч")
        assert request.query == "Нужна гитара для металла до 45 тысяч"

    def test_empty_query_raises_error(self):
        """Пустой query должен вызывать ошибку валидации."""
        with pytest.raises(ValidationError):
            ChatRequest(query="")

    def test_missing_query_raises_error(self):
        """Отсутствие query должно вызывать ошибку валидации."""
        with pytest.raises(ValidationError):
            ChatRequest()

    def test_query_type_validation(self):
        """query должен быть строкой."""
        with pytest.raises(ValidationError):
            ChatRequest(query=123)

        with pytest.raises(ValidationError):
            ChatRequest(query=None)


class TestSearchResult:
    """Тесты для модели SearchResult."""

    def test_valid_search_result(self):
        """Валидный результат поиска."""
        result = SearchResult(
            id="rev_001",
            title="Fender Player Stratocaster 2023",
            price=850.0,
            image_url="https://reverb.com/image.jpg",
            listing_url="https://reverb.com/item/123"
        )
        assert result.id == "rev_001"
        assert result.title == "Fender Player Stratocaster 2023"
        assert result.price == 850.0
        assert result.currency == "USD"

    def test_missing_required_fields_raises_error(self):
        """Отсутствие обязательных полей должно вызывать ошибку."""
        with pytest.raises(ValidationError):
            SearchResult(title="Test")

        with pytest.raises(ValidationError):
            SearchResult(id="1", title="Test")

    def test_currency_default_value(self):
        """currency по умолчанию должен быть USD."""
        result = SearchResult(
            id="1",
            title="Test",
            price=100,
            image_url="https://example.com/img.jpg",
            listing_url="https://example.com/1"
        )
        assert result.currency == "USD"

    def test_custom_currency(self):
        """Можно установить кастомную валюту."""
        result = SearchResult(
            id="1",
            title="Test",
            price=100,
            currency="EUR",
            image_url="https://example.com/img.jpg",
            listing_url="https://example.com/1"
        )
        assert result.currency == "EUR"


class TestChatResponse:
    """Тесты для модели ChatResponse."""

    def test_valid_search_response(self):
        """Валидный ответ с результатами поиска."""
        response = ChatResponse(
            mode="search",
            results=[
                SearchResult(
                    id="rev_001",
                    title="Fender Stratocaster",
                    price=850,
                    image_url="https://example.com/img.jpg",
                    listing_url="https://example.com/1"
                )
            ]
        )
        assert response.mode == "search"
        assert len(response.results) == 1
        assert response.answer is None

    def test_valid_chat_response(self):
        """Валидный ответ в режиме чата."""
        response = ChatResponse(
            mode="chat",
            answer="Я понял, что вам нужна гитара для металла"
        )
        assert response.mode == "chat"
        assert response.answer == "Я понял, что вам нужна гитара для металла"
        assert response.results is None

    def test_missing_mode_raises_error(self):
        """Отсутствие mode должно вызывать ошибку."""
        with pytest.raises(ValidationError):
            ChatResponse(results=[])

    def test_mode_type_validation(self):
        """mode должен быть строкой."""
        with pytest.raises(ValidationError):
            ChatResponse(mode=123)

    def test_both_results_and_answer(self):
        """Ответ может содержать и results, и answer."""
        response = ChatResponse(
            mode="search",
            results=[
                SearchResult(
                    id="rev_001",
                    title="Test",
                    price=100,
                    image_url="https://example.com/img.jpg",
                    listing_url="https://example.com/1"
                )
            ],
            answer="Нашёл несколько вариантов"
        )
        assert response.mode == "search"
        assert response.answer is not None
        assert response.results is not None

