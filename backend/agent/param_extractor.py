"""Модуль извлечения параметров поиска из ответа LLM."""

import json
import re
from typing import Optional


def extract_params_from_llm_response(llm_response: str) -> dict:
    """Извлекает JSON с параметрами поиска из текстового ответа LLM.

    Обрабатывает:
    - Чистый JSON
    - JSON, обёрнутый в ```json ... ```
    - JSON с лишним текстом вокруг
    - Невалидный текст → fallback {"search_queries": [], "price_min": None, "price_max": None}

    Нормализация типов: строковые цены "1000" → int 1000

    Args:
        llm_response: Текстовый ответ от LLM

    Returns:
        dict с параметрами поиска или fallback
    """
    fallback = {"search_queries": [], "price_min": None, "price_max": None}

    if not llm_response or not isinstance(llm_response, str):
        return fallback

    # Попытка найти JSON в ответе
    json_str = _extract_json_from_text(llm_response)

    if not json_str:
        return fallback

    try:
        params = json.loads(json_str)
        return _normalize_params(params)
    except (json.JSONDecodeError, ValueError):
        return fallback


def _extract_json_from_text(text: str) -> Optional[str]:
    """Извлекает JSON-строку из текста.

    Ищет:
    1. JSON в markdown блоке ```json ... ```
    2. JSON в markdown блоке ``` ... ```
    3. Первый валидный JSON объект {...} в тексте
    """
    # Попытка найти JSON в markdown блоке с указанием языка
    markdown_json_pattern = r'```json\s*({[\s\S]*?})\s*```'
    match = re.search(markdown_json_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1)

    # Попытка найти JSON в markdown блоке без указания языка
    markdown_block_pattern = r'```\s*({[\s\S]*?})\s*```'
    match = re.search(markdown_block_pattern, text)
    if match:
        return match.group(1)

    # Попытка найти первый JSON объект в тексте
    json_object_pattern = r'\{[^{}]*\}'
    match = re.search(json_object_pattern, text)
    if match:
        return match.group(0)

    # Попытка найти более сложный JSON с вложенными объектами
    if '{' in text and '}' in text:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start < end:
            return text[start:end]

    return None


def _normalize_params(params: dict) -> dict:
    """Нормализует типы параметров.

    Конвертирует строковые значения цен в int.
    Добавляет недостающие ключи со значениями по умолчанию.
    """
    result = {
        "search_queries": params.get("search_queries", []),
        "price_min": params.get("price_min"),
        "price_max": params.get("price_max"),
    }

    # Конвертация цен из строки в int
    if result["price_min"] is not None:
        if isinstance(result["price_min"], str):
            try:
                result["price_min"] = int(result["price_min"])
            except ValueError:
                result["price_min"] = None
        elif isinstance(result["price_min"], (int, float)):
            result["price_min"] = int(result["price_min"])

    if result["price_max"] is not None:
        if isinstance(result["price_max"], str):
            try:
                result["price_max"] = int(result["price_max"])
            except ValueError:
                result["price_max"] = None
        elif isinstance(result["price_max"], (int, float)):
            result["price_max"] = int(result["price_max"])

    # Убедимся, что search_queries это список
    if not isinstance(result["search_queries"], list):
        result["search_queries"] = []

    return result


def build_search_prompt(user_query: str, mapping_table: str) -> str:
    """Формирует промпт для LLM с инструкцией вернуть JSON.

    Args:
        user_query: Запрос пользователя
        mapping_table: Таблица маппинга из docs/MAPPING.md

    Returns:
        Строка промпта для LLM
    """
    prompt = f"""Ты — ассистент по подбору гитар. Твоя задача — извлечь параметры поиска из запроса пользователя.

Используй следующую таблицу маппинга для преобразования абстрактных описаний звука в конкретные параметры:

{mapping_table}

Запрос пользователя:
{user_query}

Верни ответ ТОЛЬКО в формате JSON со следующей структурой:
{{
    "search_queries": ["список конкретных моделей гитар для поиска"],
    "price_min": число или null,
    "price_max": число или null
}}

Примеры правильных ответов:
{{"search_queries": ["Fender Stratocaster", "Squier Stratocaster"], "price_min": null, "price_max": 500}}
{{"search_queries": ["Gibson Les Paul"], "price_min": 1000, "price_max": 2000}}
{{"search_queries": ["Yamaha F310"], "price_min": null, "price_max": null}}

Важно: верни ТОЛЬКО JSON, без дополнительного текста."""

    return prompt
