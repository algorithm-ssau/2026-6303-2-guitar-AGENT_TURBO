"""Сценарные тесты агента по test_scenarios.md"""

import pytest
from unittest.mock import MagicMock
from backend.agent.service import interpret_query

def test_scenario_1_direct_search():
    """Сценарий 1: Прямой подбор с четкими параметрами"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"mode": "search", "params": {"search_queries": ["Fender Player Stratocaster", "Squier Classic Vibe Telecaster"], "price_max": 1000}}'
    mock_client.chat.completions.create.return_value = mock_response

    result = interpret_query("Привет! Ищу яркую электрогитару для блюза и фанка, бюджет до 1000 баксов.", llm_client=mock_client)
    assert result["mode"] == "search"
    assert result["params"]["price_max"] == 1000
    assert len(result["params"]["search_queries"]) > 0

def test_scenario_2_lack_of_data():
    """Сценарий 2: Нехватка данных"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"mode": "consultation", "answer": "Для того, чтобы подобрать гитару для метала, скажите, какой у вас бюджет?"}'
    mock_client.chat.completions.create.return_value = mock_response

    result = interpret_query("Хочу купить гитару для метала.", llm_client=mock_client)
    assert result["mode"] == "consultation"
    assert "бюджет" in result["answer"]

def test_scenario_3_theory():
    """Сценарий 3: Теоретический вопрос"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"mode": "consultation", "answer": "Синглы звучат ярче, а хамбакеры плотнее и меньше фонят."}'
    mock_client.chat.completions.create.return_value = mock_response

    result = interpret_query("Чем отличаются синглы от хамбакеров?", llm_client=mock_client)
    assert result["mode"] == "consultation"
    assert "Синглы" in result["answer"]

def test_scenario_4_out_of_scope():
    """Сценарий 4: Выход за рамки компетенции"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"mode": "consultation", "answer": "Извините, я специализируюсь только на подборе гитар и звуке."}'
    mock_client.chat.completions.create.return_value = mock_response

    result = interpret_query("Как сгенерировать картинку в Midjourney?", llm_client=mock_client)
    assert result["mode"] == "consultation"
    assert "Извините" in result["answer"]

def test_scenario_5_acoustic():
    """Сценарий 5: Акустическая гитара"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"mode": "search", "params": {"search_queries": ["Yamaha F310", "Fender CD-60"], "price_max": 200}}'
    mock_client.chat.completions.create.return_value = mock_response

    result = interpret_query("Нужна гитара для костра петь песни, недорогая, до 200 долларов.", llm_client=mock_client)
    assert result["mode"] == "search"
    assert result["params"]["price_max"] == 200

def test_scenario_6_contradiction():
    """Сценарий 6: Противоречивый запрос"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"mode": "consultation", "answer": "Акустических гитар с такой комплектацией не выпускают. Могу предложить электрогитару."}'
    mock_client.chat.completions.create.return_value = mock_response

    result = interpret_query("Хочу акустическую гитару с флойд роузом и активными звукоснимателями EMG.", llm_client=mock_client)
    assert result["mode"] == "consultation"
    assert "Акустических" in result["answer"]
