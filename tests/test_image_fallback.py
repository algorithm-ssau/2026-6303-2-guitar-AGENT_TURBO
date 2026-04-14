"""Тесты fallback-картинок в Reverb-ответах."""

import pytest

from backend.search.search_reverb import _normalize_reverb_response

PLACEHOLDER = "https://placehold.co/400x300?text=No+Image"


def test_no_image_url_returns_placeholder():
    """Результат без image_url → плейсхолдер."""
    listing = {"id": "1", "title": "Guitar", "price": 100}
    result = _normalize_reverb_response(listing)
    assert result["image_url"] == PLACEHOLDER


def test_empty_string_image_returns_placeholder():
    """Результат с пустой строкой image_url → плейсхолдер."""
    listing = {"id": "1", "title": "Guitar", "price": 100, "image_url": ""}
    result = _normalize_reverb_response(listing)
    assert result["image_url"] == PLACEHOLDER


def test_invalid_url_returns_placeholder():
    """Результат с невалидным image_url → плейсхолдер."""
    listing = {"id": "1", "title": "Guitar", "price": 100, "image_url": "not-a-url"}
    result = _normalize_reverb_response(listing)
    assert result["image_url"] == PLACEHOLDER


def test_valid_url_preserved():
    """Результат с валидным https:// image_url → оригинал без изменений."""
    url = "https://example.com/guitar.jpg"
    listing = {"id": "1", "title": "Guitar", "price": 100, "image_url": url}
    result = _normalize_reverb_response(listing)
    assert result["image_url"] == url


def test_http_url_preserved():
    """Результат с http:// image_url → оригинал без изменений."""
    url = "http://example.com/guitar.png"
    listing = {"id": "1", "title": "Guitar", "price": 100, "image_url": url}
    result = _normalize_reverb_response(listing)
    assert result["image_url"] == url


def test_links_photo_fallback():
    """Если _links.photo.href валидный — используется он."""
    url = "https://reverb.com/photo/guitar.jpg"
    listing = {
        "id": "2",
        "title": "Les Paul",
        "price": 1500,
        "_links": {"photo": {"href": url}},
    }
    result = _normalize_reverb_response(listing)
    assert result["image_url"] == url


def test_links_photo_invalid_fallback():
    """Если _links.photo.href невалидный — плейсхолдер."""
    listing = {
        "id": "2",
        "title": "Les Paul",
        "price": 1500,
        "_links": {"photo": {"href": "not-a-url"}},
    }
    result = _normalize_reverb_response(listing)
    assert result["image_url"] == PLACEHOLDER
