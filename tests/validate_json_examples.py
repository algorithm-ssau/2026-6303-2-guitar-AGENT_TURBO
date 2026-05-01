#!/usr/bin/env python3
"""Скрипт для валидации JSON-примеров API без pytest."""

import json
import os
import glob
import sys


EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "examples", "api")


def get_json_files():
    """Получить список всех JSON-файлов."""
    pattern = os.path.join(EXAMPLES_DIR, "*.json")
    files = glob.glob(pattern)
    if not files:
        print(f"ОШИБКА: Не найдены JSON-файлы в {EXAMPLES_DIR}")
        sys.exit(1)
    return files


def test_all_json_files_parse():
    """Проверка что все JSON-файлы валидны."""
    print("Тест: Проверка валидности всех JSON-файлов...")
    all_ok = True
    for filepath in get_json_files():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                json.load(f)
            print(f"  [OK] {os.path.basename(filepath)}")
        except json.JSONDecodeError as e:
            print(f"  [FAIL] {os.path.basename(filepath)}: {e}")
            all_ok = False
    
    if not all_ok:
        print("ОШИБКА: Некоторые файлы содержат невалидный JSON")
        sys.exit(1)
    print("  [OK] Все JSON-файлы валидны\n")


def test_request_files_have_query_field():
    """Проверка что request-файлы содержат поле query."""
    print("Тест: Проверка наличия поля 'query' в request-файлах...")
    request_files = [
        "chat_search.request.json",
        "chat_consultation.request.json",
    ]
    
    for filename in request_files:
        filepath = os.path.join(EXAMPLES_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  [FAIL] Файл {filename} не найден")
            sys.exit(1)
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "query" not in data:
                print(f"  [FAIL] Файл {filename} должен содержать поле 'query'")
                sys.exit(1)
            if not isinstance(data["query"], str) or len(data["query"]) == 0:
                print(f"  [FAIL] Поле 'query' в {filename} должно быть непустой строкой")
                sys.exit(1)
        print(f"  [OK] {filename}")
    print("  [OK] Все request-файлы корректны\n")


def test_response_files_not_empty():
    """Проверка что response-файлы не пустые."""
    print("Тест: Проверка что response-файлы не пустые...")
    response_files = [
        "chat_search.response.json",
        "chat_consultation.response.json",
        "sessions.response.json",
        "messages.response.json",
        "metrics_health.response.json",
    ]
    
    for filename in response_files:
        filepath = os.path.join(EXAMPLES_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  [FAIL] Файл {filename} не найден")
            sys.exit(1)
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not data:
                print(f"  [FAIL] Файл {filename} пустой")
                sys.exit(1)
        print(f"  [OK] {filename}")
    print("  [OK] Все response-файлы непустые\n")


def test_error_response_has_detail():
    """Проверка что error.response.json содержит поле detail."""
    print("Тест: Проверка error.response.json...")
    filepath = os.path.join(EXAMPLES_DIR, "error.response.json")
    if not os.path.exists(filepath):
        print(f"  [FAIL] Файл error.response.json не найден")
        sys.exit(1)
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        if "detail" not in data:
            print(f"  [FAIL] Файл error.response.json должен содержать поле 'detail'")
            sys.exit(1)
        if not isinstance(data["detail"], str):
            print(f"  [FAIL] Поле 'detail' должно быть строкой")
            sys.exit(1)
    print("  [OK] error.response.json корректен\n")


def test_no_placeholder_values():
    """Проверка отсутствия placeholder-значений."""
    print("Тест: Проверка отсутствия placeholder-значений...")
    placeholder_patterns = ["TODO", "...", "example.com"]
    all_ok = True
    
    for filepath in get_json_files():
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
            for pattern in placeholder_patterns:
                if pattern in content:
                    print(f"  [FAIL] Файл {os.path.basename(filepath)} содержит placeholder '{pattern}'")
                    all_ok = False
    
    if not all_ok:
        sys.exit(1)
    print("  [OK] Placeholder-значения отсутствуют\n")


def test_response_files_use_camelCase():
    """Проверка что response-файлы используют camelCase для полей."""
    print("Тест: Проверка использования camelCase в response-файлах...")
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
            data_str = json.dumps(data)
            
            # Проверяем наличие хотя бы одного camelCase поля
            found_camel = any(field in data_str for field in camelCase_fields)
            if found_camel:
                print(f"  [OK] {filename} использует camelCase")
            else:
                print(f"  [WARN] {filename} возможно не использует camelCase (предупреждение)")
    
    print("  [OK] Проверка camelCase завершена\n")


def main():
    """Запуск всех тестов."""
    print("=" * 60)
    print("Валидация JSON-примеров API")
    print("=" * 60 + "\n")
    
    test_all_json_files_parse()
    test_request_files_have_query_field()
    test_response_files_not_empty()
    test_error_response_has_detail()
    test_no_placeholder_values()
    test_response_files_use_camelCase()
    
    print("=" * 60)
    print("[SUCCESS] ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 60)


if __name__ == "__main__":
    main()
