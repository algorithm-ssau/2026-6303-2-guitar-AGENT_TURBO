"""
Интеграция с Reverb API для поиска гитар.

Функция используется другими модулями backend для запуска
поиска объявлений по уже подготовленным параметрам.
"""
from __future__ import annotations

import os
from typing import Any

from backend.search.mock_reverb import _filter_by_price, _search_mock_reverb
from backend.search.reverb_client import _search_reverb_api
from backend.search.synonyms import expand_queries


def search_reverb(
    search_queries: list[str],
    price_min: int | None = None,
    price_max: int | None = None,
    *,
    expand_query_synonyms: bool = True,
    type: str | None = None,
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
        expand_query_synonyms: Расширять ли запросы внутренними синонимами.

    Returns:
        Нормализованный список объявлений Reverb. Каждый элемент содержит:
        - id: идентификатор объявления
        - title: название
        - price: цена
        - currency: валюта
        - image_url: ссылка на изображение
        - listing_url: ссылка на карточку товара
    """
    # Direct callers keep synonym expansion by default. Agent-owned search can opt out
    # so router-provided effective queries stay identical to executed queries.
    search_queries = expand_queries(search_queries) if expand_query_synonyms else list(search_queries or [])

    # Проверяем режим работы
    use_mock = os.getenv("USE_MOCK_REVERB", "false").lower() == "true"

    if use_mock:
        return _search_mock_reverb(search_queries, price_min, price_max, type=type)

    # Проверяем наличие токена — если нет, fallback на mock
    api_token = os.getenv("REVERB_API_TOKEN")
    if not api_token:
        return _search_mock_reverb(search_queries, price_min, price_max, type=type)

    # Реальный режим: делаем запрос к API с авторизацией
    results = _search_reverb_api(search_queries, price_min, price_max)

    # Фильтруем результаты по цене
    results = _filter_by_price(results, price_min, price_max)

    # Если API вернул пустой результат, используем мок-данные как fallback
    if not results:
        results = _search_mock_reverb(search_queries, price_min, price_max, type=type)

    return results


def search_reverb_exact(
    search_queries: list[str],
    price_min: int | None = None,
    price_max: int | None = None,
    *,
    type: str | None = None,
) -> list[dict[str, Any]]:
    """Executes Reverb search without post-router synonym expansion."""
    return search_reverb(
        search_queries,
        price_min,
        price_max,
        expand_query_synonyms=False,
        type=type,
    )
