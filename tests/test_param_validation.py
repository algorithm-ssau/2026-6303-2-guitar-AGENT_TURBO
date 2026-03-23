"""Тесты валидации извлечённых параметров поиска."""

import pytest
from backend.agent.param_extractor import extract_params_from_llm_response


@pytest.mark.parametrize(
    "llm_response, expected_queries, expected_price_min, expected_price_max",
    [
        # 1. Запрос с бюджетом и типом гитары
        (
            '{"search_queries": ["Fender Stratocaster", "Squier Stratocaster"], "price_min": null, "price_max": 500}',
            ["Fender Stratocaster", "Squier Stratocaster"],
            None,
            500,
        ),
        # 2. Запрос с диапазоном цен
        (
            '{"search_queries": ["Gibson Les Paul"], "price_min": 1000, "price_max": 2000}',
            ["Gibson Les Paul"],
            1000,
            2000,
        ),
        # 3. Запрос с типом гитары (акустика)
        (
            '{"search_queries": ["Yamaha F310", "Fender CD-60"], "price_min": null, "price_max": 300}',
            ["Yamaha F310", "Fender CD-60"],
            None,
            300,
        ),
        # 4. Запрос для метала с активными звукоснимателями
        (
            '{"search_queries": ["Ibanez RG", "Jackson Dinky"], "price_min": 400, "price_max": 800}',
            ["Ibanez RG", "Jackson Dinky"],
            400,
            800,
        ),
        # 5. Запрос с универсальной гитарой (HSS)
        (
            '{"search_queries": ["Yamaha Pacifica", "Ibanez AZ"], "price_min": null, "price_max": 600}',
            ["Yamaha Pacifica", "Ibanez AZ"],
            None,
            600,
        ),
        # 6. Запрос с винтажной гитарой
        (
            '{"search_queries": ["Fender Vintera", "Squier Classic Vibe"], "price_min": 500, "price_max": 1200}',
            ["Fender Vintera", "Squier Classic Vibe"],
            500,
            1200,
        ),
        # 7. Запрос с 7-струнной гитарой для djent
        (
            '{"search_queries": ["Ibanez GRG7", "ESP LTD SC-607"], "price_min": 600, "price_max": 1000}',
            ["Ibanez GRG7", "ESP LTD SC-607"],
            600,
            1000,
        ),
    ],
    ids=[
        "search_stratocaster_budget",
        "search_les_paul_range",
        "search_acoustic_budget",
        "search_metal_range",
        "search_universal_hss",
        "search_vintage_range",
        "search_7string_djent",
    ],
)
def test_param_extraction(llm_response: str, expected_queries: list, expected_price_min: int, expected_price_max: int):
    """Проверяет корректность извлечения параметров из ответа LLM."""
    result = extract_params_from_llm_response(llm_response)
    
    assert result["search_queries"] == expected_queries
    assert result["price_min"] == expected_price_min
    assert result["price_max"] == expected_price_max
