"""Тесты детектора режима — 7 примеров из docs/MODE_DETECTION.md."""

import pytest
from backend.agent.mode_detector import detect_mode


@pytest.mark.parametrize(
    "query, expected_mode",
    [
        # 1. Явный запрос на подбор + бюджет + стиль
        (
            "Подбери электрогитару до 1200$ для блюза, чтобы звук был теплый.",
            "search",
        ),
        # 2. Теоретический вопрос без запроса на покупку
        (
            "В чем разница между single-coil и humbucker?",
            "consultation",
        ),
        # 3. Запрос на варианты с ограничениями
        (
            "Хочу что-то для джаза, бюджет до 90 тысяч, покажи варианты.",
            "search",
        ),
        # 4. Обучающий вопрос про влияние параметров
        (
            "Как дерево корпуса влияет на сустейн?",
            "consultation",
        ),
        # 5. Сравнение и консультация без запроса товаров
        (
            "Что лучше для метала: EMG или пассивные датчики?",
            "consultation",
        ),
        # 6. Конкретные критерии выбора инструмента
        (
            "Нужна 7-струнная гитара для djent, желательно Ibanez.",
            "search",
        ),
        # 7. Рекомендация по подходу, а не список лотов
        (
            "Я новичок: с чего начать выбор первой электрогитары?",
            "consultation",
        ),
    ],
    ids=[
        "search_blues_budget",
        "consultation_pickup_diff",
        "search_jazz_budget",
        "consultation_wood_sustain",
        "consultation_emg_vs_passive",
        "search_7string_djent",
        "consultation_beginner",
    ],
)
def test_mode_detection(query: str, expected_mode: str):
    """Проверяет правильность определения режима для примеров из документации."""
    assert detect_mode(query) == expected_mode
