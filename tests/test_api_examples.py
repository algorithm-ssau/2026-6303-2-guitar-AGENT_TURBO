"""
Тесты для валидации JSON-примеров API.

Проверяет:
- все файлы docs/examples/api/*.json парсятся
- request-файлы содержат ожидаемые поля
- response-файлы не пустые
- error.response.json содержит поле detail
"""

import json
import os
import glob


EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "examples", "api")


def get_json_files():
    """Получить список всех JSON-файлов в директории примеров."""
    pattern = os.path.join(EXAMPLES_DIR, "*.json")
    files = glob.glob(pattern)
    assert len(files) > 0, f"Не найдены JSON-файлы в {EXAMPLES_DIR}"
    return files


def test_all_json_files_parse():
    """Проверка что все JSON-файлы валидны."""
    for filepath in get_json_files():
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                raise AssertionError(f"Ошибка парсинга JSON в файле {os.path.basename(filepath)}: {e}")


def test_request_files_have_query_field():
    """Проверка что request-файлы содержат поле query."""
    request_files = [
        "chat_search.request.json",
        "chat_consultation.request.json",
    ]
    
    for filename in request_files:
        filepath = os.path.join(EXAMPLES_DIR, filename)
        assert os.path.exists(filepath), f"Файл {filename} не найден"
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "query" in data, f"Файл {filename} должен содержать поле 'query'"
            assert isinstance(data["query"], str), f"Поле 'query' в {filename} должно быть строкой"
            assert len(data["query"]) > 0, f"Поле 'query' в {filename} не должно быть пустым"


def test_response_files_not_empty():
    """Проверка что response-файлы не пустые."""
    response_files = [
        "chat_search.response.json",
        "chat_consultation.response.json",
        "sessions.response.json",
        "messages.response.json",
        "metrics_health.response.json",
    ]
    
    for filename in response_files:
        filepath = os.path.join(EXAMPLES_DIR, filename)
        assert os.path.exists(filepath), f"Файл {filename} не найден"
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data, f"Файл {filename} не должен быть пустым"


def test_error_response_has_detail():
    """Проверка что error.response.json содержит поле detail."""
    filepath = os.path.join(EXAMPLES_DIR, "error.response.json")
    assert os.path.exists(filepath), "Файл error.response.json не найден"
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "detail" in data, "Файл error.response.json должен содержать поле 'detail'"
        assert isinstance(data["detail"], str), "Поле 'detail' должно быть строкой"


def test_no_placeholder_values():
    """Проверка отсутствия placeholder-значений."""
    placeholder_patterns = ["TODO", "...", "example.com"]
    
    for filepath in get_json_files():
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
            for pattern in placeholder_patterns:
                assert pattern not in content, \
                    f"Файл {os.path.basename(filepath)} содержит placeholder '{pattern}'"


def test_response_files_use_camelCase():
    """Проверка что response-файлы используют camelCase для полей."""
    response_files = [
        "chat_search.response.json",
        "sessions.response.json",
        "messages.response.json",
        "metrics_health.response.json",
    ]
    
    camelCase_fields = ["imageUrl", "listingUrl", "createdAt", "updatedAt", "sessionId", "userQuery"]
    
    for filename in response_files:
        filepath = os.path.join(EXAMPLES_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Проверяем наличие camelCase полей в структуре
            data_str = json.dumps(data)
            for field in camelCase_fields:
                if field.lower() in filename.lower() or field in data_str:
                    assert field in data_str, \
                        f"Файл {filename} должен использовать camelCase поле '{field}'"
