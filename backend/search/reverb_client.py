"""Низкоуровневый HTTP-клиент Reverb API."""
from __future__ import annotations

import os
import time
from typing import Any

import requests

from backend.search.reverb_normalizer import _deduplicate_listings, _normalize_reverb_response
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
