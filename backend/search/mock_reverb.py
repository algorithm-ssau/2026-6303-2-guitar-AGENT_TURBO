"""Локальный mock-поиск Reverb для degraded/mock режима."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _get_mock_data_path() -> Path:
    """Возвращает путь к файлу с мок-данными."""
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

    queries_lower = [q.lower() for q in search_queries]

    result = []
    for item in listings:
        title_lower = item.get("title", "").lower()
        for query in queries_lower:
            words = query.split()
            if all(word in title_lower for word in words):
                result.append(item)
                break

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


def _filter_by_type(
    listings: list[dict[str, Any]],
    type_value: str | None,
) -> list[dict[str, Any]]:
    """Фильтрует по category. None или 'any' = без фильтра.
    Маппинг type → допустимые category-значения."""
    if not type_value or str(type_value).strip().lower() == "any":
        return listings
    t = str(type_value).strip().lower()
    # Электрогитарные типы все попадают в category=electric
    electric_types = {"stratocaster", "telecaster", "les paul", "sg", "superstrat", "seven_string"}
    if t in electric_types:
        wanted = {"electric"}
    elif t in {"acoustic"}:
        wanted = {"acoustic"}
    elif t in {"classical"}:
        wanted = {"classical"}
    elif t in {"bass"}:
        wanted = {"bass"}
    else:
        return listings
    return [item for item in listings if str(item.get("category", "")).strip().lower() in wanted]


def _search_mock_reverb(
    search_queries: list[str],
    price_min: int | None,
    price_max: int | None,
    *,
    type: str | None = None,
) -> list[dict[str, Any]]:
    """Возвращает mock-результаты с теми же фильтрами, что и основной поиск."""
    mock_data = _load_mock_data()
    mock_data = _filter_by_type(mock_data, type)
    filtered_by_query = _filter_by_queries(mock_data, search_queries)
    return _filter_by_price(filtered_by_query, price_min, price_max)
