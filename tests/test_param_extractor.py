"""Тесты модуля извлечения параметров param_extractor."""

import pytest
from backend.agent.param_extractor import extract_params_from_llm_response, build_search_prompt


class TestExtractParamsFromLlmResponse:
    """Тесты функции extract_params_from_llm_response."""

    def test_clean_json(self):
        """Тест: чистый JSON без обёрток."""
        response = '{"search_queries": ["Fender Stratocaster"], "price_min": 500, "price_max": 1000}'
        result = extract_params_from_llm_response(response)
        
        assert result["search_queries"] == ["Fender Stratocaster"]
        assert result["price_min"] == 500
        assert result["price_max"] == 1000

    def test_markdown_json_block(self):
        """Тест: JSON в markdown блоке с указанием языка."""
        response = '''Вот результат:
```json
{"search_queries": ["Gibson Les Paul"], "price_min": 1500, "price_max": 2500}
```
'''
        result = extract_params_from_llm_response(response)
        
        assert result["search_queries"] == ["Gibson Les Paul"]
        assert result["price_min"] == 1500
        assert result["price_max"] == 2500

    def test_markdown_block_no_language(self):
        """Тест: JSON в markdown блоке без указания языка."""
        response = '''```
{"search_queries": ["Yamaha F310"], "price_min": null, "price_max": 300}
```'''
        result = extract_params_from_llm_response(response)
        
        assert result["search_queries"] == ["Yamaha F310"]
        assert result["price_min"] is None
        assert result["price_max"] == 300

    def test_json_with_text_around(self):
        """Тест: JSON с лишним текстом вокруг."""
        response = '''Я проанализировал ваш запрос и вот что рекомендую:
Используйте эти параметры для поиска:
{"search_queries": ["Ibanez RG", "Jackson Dinky"], "price_min": 400, "price_max": 800}
Надеюсь, это поможет!'''
        result = extract_params_from_llm_response(response)
        
        assert result["search_queries"] == ["Ibanez RG", "Jackson Dinky"]
        assert result["price_min"] == 400
        assert result["price_max"] == 800

    def test_invalid_json_fallback(self):
        """Тест: невалидный JSON возвращает fallback."""
        response = "Это просто какой-то текст без JSON"
        result = extract_params_from_llm_response(response)
        
        assert result == {"search_queries": [], "price_min": None, "price_max": None}

    def test_empty_string_fallback(self):
        """Тест: пустая строка возвращает fallback."""
        result = extract_params_from_llm_response("")
        
        assert result == {"search_queries": [], "price_min": None, "price_max": None}

    def test_none_fallback(self):
        """Тест: None возвращает fallback."""
        result = extract_params_from_llm_response(None)
        
        assert result == {"search_queries": [], "price_min": None, "price_max": None}

    def test_string_price_conversion(self):
        """Тест: конвертация строковых цен в int."""
        response = '{"search_queries": ["Epiphone SG"], "price_min": "300", "price_max": "600"}'
        result = extract_params_from_llm_response(response)
        
        assert result["search_queries"] == ["Epiphone SG"]
        assert result["price_min"] == 300
        assert result["price_max"] == 600
        assert isinstance(result["price_min"], int)
        assert isinstance(result["price_max"], int)

    def test_preserves_type_brand_and_pickups(self):
        """Доп. поля не должны теряться до этапа clarification/ranking."""
        response = '{"search_queries": ["Fender Stratocaster"], "price_max": 1200, "type": "Stratocaster", "brand": "Fender", "pickups": "SSS"}'
        result = extract_params_from_llm_response(response)

        assert result["type"] == "Stratocaster"
        assert result["brand"] == "Fender"
        assert result["pickups"] == "SSS"


class TestBuildSearchPrompt:
    """Тесты функции build_search_prompt."""

    def test_build_search_prompt_contains_user_query(self):
        """Тест: промпт включает запрос пользователя."""
        user_query = "Хочу гитару для блюза до 1000$"
        mapping_table = "| Эпитет | Параметр |\n|--------|----------|\n| Тёплый | Хамбакер |"
        
        prompt = build_search_prompt(user_query, mapping_table)
        
        assert user_query in prompt

    def test_build_search_prompt_contains_mapping(self):
        """Тест: промпт включает таблицу маппинга."""
        user_query = "Хочу гитару для блюза"
        mapping_table = "| Эпитет | Параметр |\n|--------|----------|\n| Тёплый | Хамбакер |"
        
        prompt = build_search_prompt(user_query, mapping_table)
        
        assert mapping_table in prompt

    def test_build_search_prompt_structure(self):
        """Тест: промпт содержит инструкцию вернуть JSON."""
        user_query = "Тестовый запрос"
        mapping_table = "Таблица маппинга"
        
        prompt = build_search_prompt(user_query, mapping_table)
        
        assert "JSON" in prompt
        assert "search_queries" in prompt
        assert "price_min" in prompt
        assert "price_max" in prompt
