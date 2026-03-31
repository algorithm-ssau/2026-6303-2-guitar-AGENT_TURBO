"""Тесты для модуля сериализации snake_case ↔ camelCase."""

import pytest
from backend.utils.serializer import snake_to_camel


def test_snake_to_camel_single_field():
    """Преобразование одного поля image_url → imageUrl."""
    data = {"image_url": "https://example.com/image.jpg"}
    result = snake_to_camel(data)
    assert result == {"imageUrl": "https://example.com/image.jpg"}


def test_snake_to_camel_listing_url():
    """Преобразование поля listing_url → listingUrl."""
    data = {"listing_url": "https://reverb.com/item/123"}
    result = snake_to_camel(data)
    assert result == {"listingUrl": "https://reverb.com/item/123"}


def test_snake_to_camel_multiple_fields():
    """Преобразование нескольких полей одновременно."""
    data = {
        "image_url": "https://example.com/image.jpg",
        "listing_url": "https://reverb.com/item/123",
        "title": "Fender Stratocaster",
        "price": 1500.00
    }
    result = snake_to_camel(data)
    assert result == {
        "imageUrl": "https://example.com/image.jpg",
        "listingUrl": "https://reverb.com/item/123",
        "title": "Fender Stratocaster",
        "price": 1500.00
    }


def test_snake_to_camel_list_of_results():
    """Преобразование списка из 3 результатов."""
    data = [
        {
            "id": "1",
            "title": "Fender Stratocaster",
            "price": 1500.00,
            "currency": "USD",
            "image_url": "https://example.com/image1.jpg",
            "listing_url": "https://reverb.com/item/1"
        },
        {
            "id": "2",
            "title": "Gibson Les Paul",
            "price": 2500.00,
            "currency": "USD",
            "image_url": "https://example.com/image2.jpg",
            "listing_url": "https://reverb.com/item/2"
        },
        {
            "id": "3",
            "title": "Ibanez RG",
            "price": 800.00,
            "currency": "USD",
            "image_url": "https://example.com/image3.jpg",
            "listing_url": "https://reverb.com/item/3"
        }
    ]
    result = snake_to_camel(data)
    
    assert len(result) == 3
    assert result[0] == {
        "id": "1",
        "title": "Fender Stratocaster",
        "price": 1500.00,
        "currency": "USD",
        "imageUrl": "https://example.com/image1.jpg",
        "listingUrl": "https://reverb.com/item/1"
    }
    assert result[1] == {
        "id": "2",
        "title": "Gibson Les Paul",
        "price": 2500.00,
        "currency": "USD",
        "imageUrl": "https://example.com/image2.jpg",
        "listingUrl": "https://reverb.com/item/2"
    }
    assert result[2] == {
        "id": "3",
        "title": "Ibanez RG",
        "price": 800.00,
        "currency": "USD",
        "imageUrl": "https://example.com/image3.jpg",
        "listingUrl": "https://reverb.com/item/3"
    }


def test_snake_to_camel_fields_without_underscore():
    """Поля без подчёркивания остаются без изменений."""
    data = {
        "id": "1",
        "title": "Fender Stratocaster",
        "price": 1500.00,
        "currency": "USD"
    }
    result = snake_to_camel(data)
    assert result == {
        "id": "1",
        "title": "Fender Stratocaster",
        "price": 1500.00,
        "currency": "USD"
    }


def test_snake_to_camel_nested_dict():
    """Рекурсивное преобразование вложенных словарей."""
    data = {
        "guitar_info": {
            "brand_name": "Fender",
            "model_year": 2020
        },
        "price_value": 1500.00
    }
    result = snake_to_camel(data)
    assert result == {
        "guitarInfo": {
            "brandName": "Fender",
            "modelYear": 2020
        },
        "priceValue": 1500.00
    }


def test_snake_to_camel_nested_list():
    """Рекурсивное преобразование вложенных списков."""
    data = {
        "results": [
            {"image_url": "https://example.com/image1.jpg"},
            {"image_url": "https://example.com/image2.jpg"}
        ]
    }
    result = snake_to_camel(data)
    assert result == {
        "results": [
            {"imageUrl": "https://example.com/image1.jpg"},
            {"imageUrl": "https://example.com/image2.jpg"}
        ]
    }


def test_snake_to_camel_empty_dict():
    """Пустой словарь возвращается как есть."""
    data = {}
    result = snake_to_camel(data)
    assert result == {}


def test_snake_to_camel_empty_list():
    """Пустой список возвращается как есть."""
    data = []
    result = snake_to_camel(data)
    assert result == []


def test_snake_to_camel_non_dict_input():
    """Не-dict/non-list значения возвращаются как есть."""
    assert snake_to_camel("string") == "string"
    assert snake_to_camel(123) == 123
    assert snake_to_camel(None) is None
