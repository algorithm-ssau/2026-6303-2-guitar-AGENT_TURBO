"""Утилиты для сериализации данных: преобразование snake_case в camelCase."""

from typing import Any, Dict, List, Union


def snake_to_camel(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    if isinstance(data, list):
        return [snake_to_camel(item) for item in data]

    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        camel_key = _to_camel(key)

        if isinstance(value, dict):
            result[camel_key] = snake_to_camel(value)
        elif isinstance(value, list):
            result[camel_key] = snake_to_camel(value)
        else:
            result[camel_key] = value

    return result


def _to_camel(snake_str: str) -> str:
    components = snake_str.split('_')
    return components[0] + ''.join(x.capitalize() for x in components[1:])


# Entity-specific serializers

def serialize_search_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return snake_to_camel(results)


def serialize_search_params(params: Dict[str, Any]) -> Dict[str, Any]:
    return snake_to_camel(params)


def serialize_kpi_response(kpi_data: Dict[str, Any]) -> Dict[str, Any]:
    return snake_to_camel(kpi_data)
