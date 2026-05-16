"""
Интеграция с Reverb API для поиска гитар.

Функция используется другими модулями backend для запуска
поиска объявлений по уже подготовленным параметрам.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests

from backend.search.mock_reverb import _filter_by_price, _search_mock_reverb
from backend.search.reverb_normalizer import _deduplicate_listings, _normalize_reverb_response
from backend.search.synonyms import expand_queries
from backend.utils.logger import get_logger

_search_logger = get_logger("search.reverb")


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

        # Retry-цикл: максимум 3 попытки с экспоненциальным backoff
        max_retries = 3
        backoffs = [0.5, 1.0, 2.0]
        succeeded = False

        for attempt in range(max_retries):
            try:
                _search_logger.info(
                    "attempt %d/%d: GET %s query=%s",
                    attempt + 1, max_retries, url, query,
                )
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=10,
                )

                # 4xx — сразу пропускаем без ретрая
                if 400 <= response.status_code < 500:
                    _search_logger.warning(
                        "HTTP %d — пропускаем без ретрая", response.status_code,
                    )
                    break

                # 5xx — ретраим
                if response.status_code >= 500:
                    _search_logger.warning(
                        "attempt %d/%d: HTTP %d",
                        attempt + 1, max_retries, response.status_code,
                    )
                    if attempt < max_retries - 1:
                        time.sleep(backoffs[attempt])
                    continue

                # Успех (2xx)
                response.raise_for_status()
                try:
                    data = response.json()
                except ValueError as exc:
                    _search_logger.warning(
                        "attempt %d/%d: malformed JSON response: %s",
                        attempt + 1,
                        max_retries,
                        exc,
                    )
                    break

                if not isinstance(data, dict):
                    _search_logger.warning(
                        "attempt %d/%d: unexpected response format: %s",
                        attempt + 1,
                        max_retries,
                        type(data).__name__,
                    )
                    break

                # Извлекаем объявления из ответа
                listings = data.get("listings", [])
                for listing in listings:
                    normalized = _normalize_reverb_response(listing)
                    if normalized["title"]:  # Только если есть название
                        all_results.append(normalized)

                succeeded = True
                break  # выходим из retry-цикла

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
                _search_logger.warning(
                    "attempt %d/%d: %s", attempt + 1, max_retries, type(exc).__name__,
                )
                if attempt < max_retries - 1:
                    time.sleep(backoffs[attempt])
                continue

        if not succeeded:
            # Все попытки исчерпаны — пропускаем этот query
            _search_logger.warning("Все %d попытки для query='%s' исчерпаны", max_retries, query)
            continue

    # Дедупликация по id — один лот не должен появляться дважды
    return _deduplicate_listings(all_results)


def search_reverb(
    search_queries: list[str],
    price_min: int | None = None,
    price_max: int | None = None,
    *,
    expand_query_synonyms: bool = True,
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
        return _search_mock_reverb(search_queries, price_min, price_max)

    # Проверяем наличие токена — если нет, fallback на mock
    api_token = os.getenv("REVERB_API_TOKEN")
    if not api_token:
        return _search_mock_reverb(search_queries, price_min, price_max)

    # Реальный режим: делаем запрос к API с авторизацией
    results = _search_reverb_api(search_queries, price_min, price_max)

    # Фильтруем результаты по цене
    results = _filter_by_price(results, price_min, price_max)

    # Если API вернул пустой результат, используем мок-данные как fallback
    if not results:
        results = _search_mock_reverb(search_queries, price_min, price_max)

    return results


def search_reverb_exact(
    search_queries: list[str],
    price_min: int | None = None,
    price_max: int | None = None,
) -> list[dict[str, Any]]:
    """Executes Reverb search without post-router synonym expansion."""
    return search_reverb(
        search_queries,
        price_min,
        price_max,
        expand_query_synonyms=False,
    )
