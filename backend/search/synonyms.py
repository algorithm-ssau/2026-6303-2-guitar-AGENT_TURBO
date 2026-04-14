"""
Модуль синонимов для расширения поисковых запросов.

Словарь переводит сленг, сокращения и русские названия
в каноничные английские термины, используемые в заголовках Reverb.
"""
from __future__ import annotations


# Словарь синонимов: сленг/сокращение → каноничное название
# Минимум 20 записей, RU + EN
SYNONYMS: dict[str, str] = {
    # Английские сокращения и сленг
    "strat": "stratocaster",
    "tele": "telecaster",
    "lp": "les paul",
    "jazzbass": "jazz bass",
    "p bass": "precision bass",
    "precision": "precision bass",
    "precbass": "precision bass",
    "hollow body": "hollow body guitar",
    "hollow": "hollow body",
    "semi-hollow": "semi-hollow body",
    "semi hollow": "semi-hollow body",
    "superstrat": "superstrat style",
    "dread": "dreadnought",
    "dreadnought": "dreadnought acoustic",
    "parlor": "parlor acoustic",
    "ac-electric": "acoustic",
    # Русские названия и транслит
    "стратокастер": "stratocaster",
    "телекастер": "telecaster",
    "лес пол": "les paul",
    "леспол": "les paul",
    "джазбас": "jazz bass",
    "джаз бас": "jazz bass",
    "прецизионный бас": "precision bass",
    "прецизионный": "precision bass",
    "полуакустика": "semi-hollow",
    "акустика": "acoustic",
    "электричка": "electric",
    "бас": "bass",
    "хамбакер": "humbucker",
    "сингл": "single coil",
    "семиструн": "7-string",
    "7-струн": "7-string",
    "классика": "classical",
    "классическая": "classical",
    "звукосниматель": "pickup",
    "бридж": "bridge",
    "мензура": "scale",
    "накладка": "fretboard",
    "порожек": "nut",
}


def expand_queries(queries: list[str]) -> list[str]:
    """
    Расширяет список поисковых запросов синонимами.

    Для каждого запроса находит совпадения в словаре SYNONYMS
    (регистронезависимо) и добавляет каноничную форму.
    Исходные запросы сохраняются, дубликаты удаляются.

    Args:
        queries: Список исходных поисковых запросов.

    Returns:
        Расширенный список запросов без дубликатов.
    """
    if not queries:
        return []

    result: list[str] = []
    seen: set[str] = set()

    for query in queries:
        # Добавляем оригинал
        if query not in seen:
            result.append(query)
            seen.add(query)

        # Ищем синоним (регистронезависимо)
        query_lower = query.lower()
        if query_lower in SYNONYMS:
            canonical = SYNONYMS[query_lower]
            if canonical not in seen:
                result.append(canonical)
                seen.add(canonical)

    return result
