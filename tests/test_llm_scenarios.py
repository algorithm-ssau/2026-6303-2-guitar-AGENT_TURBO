"""Сценарные тесты LLM с параметризацией."""

import pytest
from unittest.mock import MagicMock
from backend.agent.service import interpret_query

scenarios = [
    # 1. Прямой подбор с четкими параметрами
    (
        "Привет! Ищу яркую электрогитару для блюза и фанка, бюджет до 1000 баксов.",
        '{"mode": "search", "params": {"search_queries": ["Fender Player Stratocaster", "Squier Classic Vibe Telecaster"], "price_max": 1000}}',
        "search"
    ),
    # 2. Нехватка данных
    (
        "Хочу купить гитару для метала.",
        '{"mode": "consultation", "answer": "Какой у вас бюджет?"}',
        "consultation"
    ),
    # 3. Теоретический вопрос
    (
        "Чем отличаются синглы от хамбакеров?",
        '{"mode": "consultation", "answer": "Синглы ярче"}',
        "consultation"
    ),
    # 4. Выход за рамки компетенции (Out of Scope)
    (
        "Как сгенерировать картинку в Midjourney?",
        '{"mode": "consultation", "answer": "Извините, я специализируюсь только на гитарах."}',
        "consultation"
    ),
    # 5. Акустическая гитара
    (
        "Нужна гитара для костра петь песни, недорогая, до 200 долларов.",
        '{"mode": "search", "params": {"search_queries": ["Yamaha F310", "Fender CD-60", "Epiphone DR-100"], "price_max": 200}}',
        "search"
    ),
    # 6. Противоречивый запрос
    (
        "Хочу акустическую гитару с флойд роузом и активными звукоснимателями EMG.",
        '{"mode": "consultation", "answer": "Акустических гитар с такой комплектацией не выпускают."}',
        "consultation"
    ),
    # 7. Запасной fallback (invalid json)
    (
        "Сломани запрос",
        '{ invalid json }',
        "consultation"
    )
]

@pytest.mark.parametrize("query, mock_response_text, expected_mode", scenarios)
def test_interpret_query_scenarios(query, mock_response_text, expected_mode):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = mock_response_text
    mock_client.chat.completions.create.return_value = mock_response
    
    # We pass the mock_client to interpret_query
    # Since search_fn isn't supported by our service.py signature anymore, we only mock LLM.
    result = interpret_query(query, llm_client=mock_client)
    
    # Assert mode is correct
    assert result["mode"] == expected_mode
    
    # Assert correct structure based on mode
    if expected_mode == "search":
        assert "params" in result
    else:
        assert "answer" in result
