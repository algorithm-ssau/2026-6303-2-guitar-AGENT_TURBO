"""Нормализация и дедупликация результатов Reverb."""
from __future__ import annotations

from typing import Any


def _normalize_reverb_response(listing: dict[str, Any]) -> dict[str, Any]:
    """
    Нормализует ответ Reverb API к единому контракту проекта.

    Args:
        listing: Сырое объявление из ответа Reverb.

    Returns:
        Нормализованное объявление с полями: id, title, price, currency, image_url, listing_url.
    """
    # Извлекаем цену — может быть числом или объектом
    raw_price = listing.get("price", 0)
    if isinstance(raw_price, dict):
        try:
            price_value = float(raw_price.get("amount", 0))
        except (ValueError, TypeError):
            price_value = 0
        currency = raw_price.get("currency", "USD")
    else:
        try:
            price_value = float(raw_price)
        except (ValueError, TypeError):
            price_value = 0
        currency = "USD"

    # Извлекаем изображение — приоритет: _links.photo.href > image_url > photos[0].url
    image_url = ""
    links = listing.get("_links", {})
    if links and "photo" in links:
        image_url = links["photo"].get("href", "")
    if not image_url:
        image_url = listing.get("image_url", "")
    if not image_url:
        photos = listing.get("photos", [])
        if photos:
            image_url = photos[0].get("url", "")

    # Fallback: если image_url пустой или невалидный — подставляем плейсхолдер
    if not image_url or not image_url.startswith("http"):
        image_url = "https://placehold.co/400x300?text=No+Image"

    # Извлекаем URL листинга — приоритет: _links.web.href > url > web_url
    listing_url = ""
    if links and "web" in links:
        listing_url = links["web"].get("href", "")
    if not listing_url:
        listing_url = listing.get("url", listing.get("web_url", ""))

    return {
        "id": str(listing.get("id", "")),
        "title": listing.get("title", listing.get("name", "")),
        "price": price_value,
        "currency": currency,
        "image_url": image_url,
        "listing_url": listing_url,
    }


def _deduplicate_listings(
    listings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Удаляет дубликаты объявлений по полю id.

    Args:
        listings: Список нормализованных объявлений.

    Returns:
        Список объявлений без дубликатов (первое вхождение сохраняется).
    """
    seen_ids: set[str] = set()
    result = []
    for item in listings:
        item_id = item.get("id", "")
        if item_id not in seen_ids:
            seen_ids.add(item_id)
            result.append(item)
    return result
