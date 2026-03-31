"""Утилиты для сериализации данных: преобразование snake_case ↔ camelCase."""

from typing import Any, Dict, List, Union


def snake_to_camel(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Преобразует ключи словаря из snake_case в camelCase.

    Args:
        data: Словарь или список словарей с ключами в snake_case

    Returns:
        Словарь или список словарей с ключами в camelCase

    Пример:
        >>> snake_to_camel({"image_url": "..."})
        {"imageUrl": "..."}
        >>> snake_to_camel({"listing_url": "...", "title": "..."})
        {"listingUrl": "...", "title": "..."}
    """
    if isinstance(data, list):
        return [snake_to_camel(item) for item in data]

    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        # Преобразуем ключ из snake_case в camelCase
        camel_key = _to_camel(key)

        # Рекурсивно обрабатываем вложенные структуры
        if isinstance(value, dict):
            result[camel_key] = snake_to_camel(value)
        elif isinstance(value, list):
            result[camel_key] = snake_to_camel(value)
        else:
            result[camel_key] = value

    return result


def _to_camel(snake_str: str) -> str:
    """
    Преобразует строку из snake_case в camelCase.

    Args:
        snake_str: Строка в snake_case

    Returns:
        Строка в camelCase
    """
    components = snake_str.split('_')
    # Первый компонент остаётся с маленькой буквы, остальные с большой
    return components[0] + ''.join(x.capitalize() for x in components[1:])
