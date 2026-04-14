"""Модуль логики уточняющих вопросов для мультишагового диалога.

Если пользователь прислал запрос без достаточных данных для поиска,
агент задаёт уточняющий вопрос вместо выполнения поиска.
"""

from typing import Optional


# Шаблоны уточняющих вопросов
CLARIFICATION_QUESTIONS = {
    "budget": "Какой у вас бюджет? Укажите желаемую сумму в долларах (например, 'до 500$' или '300-800$').",
    "type": "Какой тип гитары ищете? Например: Stratocaster, Telecaster, Les Paul, SG, акустическая и т.д.",
    "both": "Уточните, пожалуйста: какой у вас бюджет и какой тип гитары вы ищете? (например, 'Stratocaster до 500$')",
}


def check_needs_clarification(params: dict) -> Optional[str]:
    """Проверяет, нужно ли задать уточняющий вопрос.

    Принимает извлечённые search_params и возвращает текст вопроса,
    если данных недостаточно для поиска.

    Args:
        params: Словарь параметров поиска (budget_max, type, search_queries)

    Returns:
        Текст уточняющего вопроса или None (если данных достаточно)

    Логика:
        - Нет бюджета И нет типа → "both"
        - Нет бюджета → "budget"
        - Нет типа → "type"
        - Пустые search_queries → "type" (если тип есть, но нет запросов — тоже проблема)
        - Всё есть → None
    """
    budget_max = params.get("budget_max") or params.get("price_max")
    guitar_type = params.get("type")
    search_queries = params.get("search_queries", [])

    # Определяем что отсутствует
    has_budget = budget_max is not None and budget_max > 0
    has_type = guitar_type is not None and str(guitar_type).strip() != ""
    has_queries = isinstance(search_queries, list) and len(search_queries) > 0

    # Если всё есть — уточнение не нужно
    if has_budget and has_type and has_queries:
        return None

    # Формируем вопрос в зависимости от того, чего не хватает
    if not has_budget and not has_type:
        return CLARIFICATION_QUESTIONS["both"]
    elif not has_budget:
        return CLARIFICATION_QUESTIONS["budget"]
    elif not has_type:
        return CLARIFICATION_QUESTIONS["type"]
    else:
        # Есть тип и бюджет но нет search_queries — маловероятно но обработаем
        return CLARIFICATION_QUESTIONS["type"]
