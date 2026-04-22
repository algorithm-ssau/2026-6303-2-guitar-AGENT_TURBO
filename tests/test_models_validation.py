import pytest
from pydantic import ValidationError
from backend.search.models import ChatRequest, GuitarResult

def test_chat_request_validation():
    # Валидный запрос
    assert ChatRequest(query="Fender").query == "Fender"
    # Слишком короткий
    with pytest.raises(ValidationError):
        ChatRequest(query="a")
    # Слишком длинный
    with pytest.raises(ValidationError):
        ChatRequest(query="x" * 501)

def test_guitar_result_validation():
    valid_data = {
        "title": "Strat",
        "price": 500,
        "currency": "USD",
        "listing_url": "https://reverb.com/item/1"
    }
    # Позитивный кейс
    assert GuitarResult(**valid_data).price == 500
    
    # Негативный: цена меньше 0
    with pytest.raises(ValidationError):
        GuitarResult(**{**valid_data, "price": -1})
    
    # Негативный: плохая валюта
    with pytest.raises(ValidationError):
        GuitarResult(**{**valid_data, "currency": "BITCOIN"})
        
    # Негативный: плохой URL
    with pytest.raises(ValidationError):
        GuitarResult(**{**valid_data, "listing_url": "not-a-link"})