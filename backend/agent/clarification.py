"""Модуль логики уточняющих вопросов для мультишагового диалога.

Если пользователь прислал запрос без достаточных данных для поиска,
агент задаёт уточняющий вопрос вместо выполнения поиска.
"""

import re
from typing import Optional


# Шаблоны уточняющих вопросов
CLARIFICATION_QUESTIONS = {
    "budget": "Какой у вас бюджет? Укажите желаемую сумму в долларах (например, 'до 500$' или '300-800$').",
    "type": "Какой тип гитары ищете? Например: Stratocaster, Telecaster, Les Paul, SG, акустическая и т.д.",
    "both": "Уточните, пожалуйста: какой у вас бюджет и какой тип гитары вы ищете? (например, 'Stratocaster до 500$')",
}

NO_PREFERENCE_MARKERS = {
    "any",
    "any type",
    "no preference",
    "не важно",
    "неважно",
    "без разницы",
    "все равно",
    "всё равно",
    "любой",
    "любая",
    "любой тип",
    "мне не важно",
    "мне неважно",
    "мне без разницы",
    "мне все равно",
    "мне всё равно",
    "мне всеравно",
    "мне всёравно",
    "пофиг",
    "мне пофиг",
    "да мне пофиг",
    "мне по барабану",
    "по барабану",
    "не принципиально",
    "что угодно",
    "любой подойдет",
    "любой подойдёт",
    "любой сойдет",
    "любой сойдёт",
    "какая угодно",
    "какой угодно",
    "что-нибудь",
    "что нибудь",
    "хоть что",
    "хоть какая",
    "хоть какой",
    "похуй",
    "да похуй",
    "мне похуй",
    "вообще пофиг",
    "вообще похуй",
    "похер",
    "мне похер",
    "похрен",
    "мне похрен",
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
        - Если есть хоть один осмысленный критерий поиска, уточнение не нужно
        - Если запрос полностью пустой и без критериев → вопрос "both"
    """
    budget_max = params.get("budget_max") or params.get("price_max")
    guitar_type = params.get("type")
    search_queries = params.get("search_queries", [])

    brand = str(params.get("brand") or "").strip()
    pickups = str(params.get("pickups") or "").strip()
    sound = str(params.get("sound") or "").strip()
    style = str(params.get("style") or "").strip()

    # Определяем что отсутствует
    has_budget = budget_max is not None and budget_max > 0
    has_type = _has_type_preference(guitar_type)
    has_queries = isinstance(search_queries, list) and len(search_queries) > 0
    has_specific_query = _has_specific_search_query(search_queries)
    allows_any_type = _is_no_preference(guitar_type)
    has_other_filters = any([brand, pickups, sound, style])

    # Для поиска достаточно любой осмысленной зацепки.
    # Уточняем только полностью пустой запрос без критериев.
    if has_budget or has_type or has_queries or has_specific_query or allows_any_type or has_other_filters:
        return None

    return CLARIFICATION_QUESTIONS["both"]


def _has_specific_search_query(search_queries: list) -> bool:
    """Проверяет, что search_queries уже содержат конкретный инструмент, а не общий мусор."""
    if not isinstance(search_queries, list):
        return False

    generic_queries = {
        "guitar", "guitars", "electric guitar", "acoustic guitar",
        "гитара", "электрогитара", "акустическая гитара",
    }

    for query in search_queries:
        normalized = str(query or "").strip().lower()
        if not normalized or normalized in generic_queries:
            continue

        # Две и более смысловые части обычно уже означают бренд+модель или форму.
        if len(normalized.split()) >= 2:
            return True

        if normalized in {"stratocaster", "telecaster", "les paul", "sg", "superstrat"}:
            return True

    return False


def _is_no_preference(value: object) -> bool:
    """Пользователь явно разрешил искать без жёсткого ограничения по полю."""
    normalized = str(value or "").strip().lower()
    if normalized in NO_PREFERENCE_MARKERS:
        return True

    patterns = [
        r"не\s*важно",
        r"без\s*разницы",
        r"вс[её]\s*равно",
        r"всеравно",
        r"всёравно",
        r"пофиг",
        r"по\s*барабану",
        r"не\s*принципиально",
        r"что\s*угодно",
        r"кака(я|[йг])\s*угодно",
        r"хоть\s*что",
        r"пох(уй|ер|рен)",
        r"любой.*под[ое]йд[её]т",
        r"любой.*с[ое]йд[её]т",
        r"любой",
        r"любая",
        r"no\s*preference",
        r"any\b",
    ]
    return any(re.search(pattern, normalized) for pattern in patterns)


def _has_type_preference(guitar_type: object) -> bool:
    """Есть ли конкретный тип, а не ответ 'любой/без разницы'."""
    normalized = str(guitar_type or "").strip().lower()
    return bool(normalized) and normalized not in NO_PREFERENCE_MARKERS
