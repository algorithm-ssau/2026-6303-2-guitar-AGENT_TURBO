"""
Сервис поиска гитар с ранжированием результатов.

Интегрирует поиск на Reverb с алгоритмом ранжирования.
"""

import json
import os
from pathlib import Path
from backend.ranking.ranking import rank_results
from backend.search.utils import enrich_guitar_data


def load_mock_data() -> list:
    """
    Загружает mock-данные из tests/mock_reverb.json.

    Returns:
        Список словарей с данными гитар
    """
    # Определяем путь к файлу относительно корня проекта
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    mock_path = project_root / 'tests' / 'mock_reverb.json'

    with open(mock_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def search_and_rank(params: dict) -> list:
    """
    Пайплайн поиска и ранжирования гитар.

    1. Загружает mock-данные (пока search_reverb() не реализован)
    2. Фильтрует по бюджету (price_min, price_max)
    3. Обогащает данные (извлекает type, pickups, brand из title)
    4. Ранжирует результаты по параметрам пользователя
    5. Возвращает топ-5

    Args:
        params: Параметры поиска:
            - budget_max: максимальная цена (опционально)
            - budget_min: минимальная цена (опционально)
            - type: тип гитары (опционально)
            - pickups: конфигурация датчиков (опционально)
            - brand: бренд (опционально)
            - country: страна производства (опционально)

    Returns:
        Топ-5 отсортированных результатов с полем score
    """
    # 1. Загружаем mock-данные
    raw_results = load_mock_data()

    # 2. Фильтруем по бюджету (базовая фильтрация до ранжирования)
    filtered_results = []
    for guitar in raw_results:
        price = guitar.get('price', 0)

        # Фильтр по максимальному бюджету
        if params.get('budget_max') is not None:
            if price > params['budget_max'] * 1.2:  # допускаем превышение на 20%
                continue

        # Фильтр по минимальному бюджету
        if params.get('budget_min') is not None:
            if price < params['budget_min']:
                continue

        filtered_results.append(guitar)

    # 3. Обогащаем данные (извлекаем type, pickups, brand из title)
    enriched_results = [enrich_guitar_data(g) for g in filtered_results]

    # 4. Ранжируем результаты
    ranked_results = rank_results(enriched_results, params)

    # 5. Возвращаем топ-5
    return ranked_results
