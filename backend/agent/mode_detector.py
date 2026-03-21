"""Детектор режима: определяет search или consultation по тексту запроса."""

import re


# Сигналы режима search — глаголы действия и намерение купить/подобрать
_SEARCH_KEYWORDS = [
    "подбери", "найди", "покажи варианты", "покажи вариант",
    "что купить", "посоветуй модель", "подборк",
    "подскажи .{0,30}до \\d",  # "подскажи Telecaster до 1500$"
    "сделай подборку",
]

# Паттерны бюджета — указание цены = намерение искать
_BUDGET_PATTERNS = [
    r"до \d+\s*\$",
    r"до \d+\s*долл",
    r"\d+\s*тысяч",
    r"бюджет",
    r"в пределах \d+",
]

# Ключевые слова, сигнализирующие намерение купить (в сочетании с контекстом)
_PURCHASE_INTENT = [
    "нужна", "нужен", "нужны",
    "хочу .{0,20}(купить|взять|приобрести|заказать)",
    "ищу",
]

# Сигналы режима consultation — вопросы про теорию, сравнения, обучение
_CONSULTATION_KEYWORDS = [
    "что лучше", "в чем разница", "в чём разница",
    "как влияет", "какой звук",
    "чем отличаются", "чем отличается",
    "почему", "как выбрать", "с чего начать",
    "что важнее", "как .{0,10} влия",
    "что значит", "что такое",
    "расскажи о ", "объясни",
]


def detect_mode(text: str) -> str:
    """Определяет режим работы агента по тексту запроса.

    Возвращает:
        "search" — если пользователь хочет подобрать конкретный инструмент
        "consultation" — если пользователь хочет разобраться в теории
    """
    if not text or not text.strip():
        return "consultation"

    lower = text.lower().strip()

    has_search = _match_any(lower, _SEARCH_KEYWORDS)
    has_budget = _match_any(lower, _BUDGET_PATTERNS)
    has_purchase = _match_any(lower, _PURCHASE_INTENT)
    has_consultation = _match_any(lower, _CONSULTATION_KEYWORDS)

    # Бюджет или покажи варианты — почти наверняка search
    if has_budget:
        return "search"

    # Явный search-сигнал
    if has_search:
        return "search"

    # Намерение купить (даже если есть consultation-сигналы — приоритет search)
    if has_purchase:
        return "search"

    # Consultation-сигналы без search-сигналов
    if has_consultation:
        return "consultation"

    # По умолчанию — consultation (безопаснее спросить, чем искать)
    return "consultation"


def _match_any(text: str, patterns: list[str]) -> bool:
    """Проверяет, содержит ли текст хотя бы один из паттернов."""
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False
