"""
Интеграция с Reverb API для поиска гитар.

Функция используется другими модулями backend для запуска
поиска объявлений по уже подготовленным параметрам.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests


def _get_mock_data_path() -> Path:
    """Возвращает путь к файлу с мок-данными."""
    # Ищем mock_reverb.json относительно корня проекта
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    return project_root / "tests" / "mock_reverb.json"


def _load_mock_data() -> list[dict[str, Any]]:
    """Загружает мок-данные из JSON файла."""
    mock_path = _get_mock_data_path()
    with open(mock_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _filter_by_queries(
    listings: list[dict[str, Any]],
    search_queries: list[str],
) -> list[dict[str, Any]]:
    """
    Фильтрует объявления по поисковым запросам (регистронезависимо).
    
    Args:
        listings: Список объявлений для фильтрации.
        search_queries: Список поисковых запросов.
    
    Returns:
        Отфильтрованный список объявлений, где title содержит хотя бы один запрос.
    """
    if not search_queries:
        return listings
    
    # Нормализуем запросы к нижнему регистру
    queries_lower = [q.lower() for q in search_queries]
    
    # Оставляем только те объявления, где title содержит хотя бы один запрос
    result = []
    for item in listings:
        title_lower = item.get("title", "").lower()
        if any(query in title_lower for query in queries_lower):
            result.append(item)
    
    return result


def _filter_by_price(
    listings: list[dict[str, Any]],
    price_min: int | None,
    price_max: int | None,
) -> list[dict[str, Any]]:
    """Фильтрует объявления по диапазону цен."""
    result = listings
    if price_min is not None:
        result = [item for item in result if item.get("price", 0) >= price_min]
    if price_max is not None:
        result = [item for item in result if item.get("price", 0) <= price_max]
    return result


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


def _search_reverb_api(
    search_queries: list[str],
    price_min: int | None = None,
    price_max: int | None = None,
) -> list[dict[str, Any]]:
    """
    Выполняет реальный запрос к Reverb API с авторизацией.

    Args:
        search_queries: Списком строк, которые нужно отправить в поиск Reverb.
        price_min: Минимальная цена.
        price_max: Максимальная цена.

    Returns:
        Список нормализованных объявлений (без дедупликации — caller делает её).
    """
    # Правильный endpoint для поиска
    url = "https://api.reverb.com/api/listings/all"

    # Читаем токен авторизации из env
    token = os.getenv("REVERB_API_TOKEN")

    # Формируем заголовки авторизации
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/hal+json",
        "Accept": "application/hal+json",
        "Accept-Version": "3.0",
    }

    all_results = []

    # Пагинация: не более 3 запросов с разными query
    max_queries = 3
    queries_to_use = search_queries[:max_queries] if search_queries else ["guitar"]

    for query in queries_to_use:
        # Формируем параметры запроса
        params = {
            "query": query,
            "limit": 10,
        }

        if price_min is not None:
            params["price_min"] = price_min
        if price_max is not None:
            params["price_max"] = price_max

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # Извлекаем объявления из ответа
            listings = data.get("listings", [])
            for listing in listings:
                normalized = _normalize_reverb_response(listing)
                if normalized["title"]:  # Только если есть название
                    all_results.append(normalized)

        except requests.exceptions.RequestException:
            # Если API недоступен, пропускаем запрос
            continue

    # Дедупликация по id — один лот не должен появляться дважды
    return _deduplicate_listings(all_results)


def search_reverb(
    search_queries: list[str],
    price_min: int | None = None,
    price_max: int | None = None,
) -> list[dict[str, Any]]:
    """
    Выполняет поиск объявлений на Reverb по подготовленным параметрам.

    Поддерживает три режима работы:
    - Мок-режим (USE_MOCK_REVERB=true): возвращает данные из mock_reverb.json
    - Реальный режим (REVERB_API_TOKEN задан): выполняет запрос к Reverb API
    - Fallback (токена нет): использует mock-данные

    Args:
        search_queries: Список строк, которые нужно отправить в поиск Reverb.
        price_min: Нижняя граница бюджета в долларах, если указана.
        price_max: Верхняя граница бюджета в долларах, если указана.

    Returns:
        Нормализованный список объявлений Reverb. Каждый элемент содержит:
        - id: идентификатор объявления
        - title: название
        - price: цена
        - currency: валюта
        - image_url: ссылка на изображение
        - listing_url: ссылка на карточку товара
    """
    # Проверяем режим работы
    use_mock = os.getenv("USE_MOCK_REVERB", "false").lower() == "true"

    if use_mock:
        # Мок-режим: загружаем данные из файла и фильтруем
        mock_data = _load_mock_data()
        # Сначала фильтруем по поисковым запросам
        filtered_by_query = _filter_by_queries(mock_data, search_queries)
        # Затем фильтруем по цене
        return _filter_by_price(filtered_by_query, price_min, price_max)

    # Проверяем наличие токена — если нет, fallback на mock
    api_token = os.getenv("REVERB_API_TOKEN")
    if not api_token:
        # Fallback: используем mock-данные как при мок-режиме
        mock_data = _load_mock_data()
        filtered_by_query = _filter_by_queries(mock_data, search_queries)
        return _filter_by_price(filtered_by_query, price_min, price_max)

    # Реальный режим: делаем запрос к API с авторизацией
    results = _search_reverb_api(search_queries, price_min, price_max)

    # Фильтруем результаты по цене
    results = _filter_by_price(results, price_min, price_max)

    # Если API вернул пустой результат, используем мок-данные как fallback
    if not results:
        mock_data = _load_mock_data()
        # Применяем фильтрацию по запросам и цене к мок-данным
        filtered_by_query = _filter_by_queries(mock_data, search_queries)
        results = _filter_by_price(filtered_by_query, price_min, price_max)

    return results
