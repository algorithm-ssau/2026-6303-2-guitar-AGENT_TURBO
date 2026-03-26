"""
Утилиты для модуля поиска.

Парсинг названий гитар для извлечения типа и конфигурации датчиков.
"""

# Маппинг ключевых слов для типов гитар
TYPE_KEYWORDS = {
    'stratocaster': 'Stratocaster',
    'strat': 'Stratocaster',
    'telecaster': 'Telecaster',
    'tele': 'Telecaster',
    'les paul': 'Les Paul',
    'lespaul': 'Les Paul',
    'lp': 'Les Paul',
    'sg': 'SG',
    'explorer': 'Explorer',
    'flying v': 'Flying V',
    'flyingv': 'Flying V',
    'custom 24': 'Custom 24',
    'rg': 'Superstrat',  # Ibanez RG серия
    'rs': 'Superstrat',  # Ibanez RS серия
    's': 'Superstrat',   # Ibanez S серия
    'az': 'Superstrat',  # Ibanez AZ серия
    'pacifica': 'Stratocaster',  # Yamaha Pacifica — страто-подобный
    'classic vibe': 'Stratocaster',  # Squier Classic Vibe — обычно страты
}

# Маппинг ключевых слов для конфигураций датчиков
PICKUPS_KEYWORDS = {
    'hss': 'HSS',
    'hsh': 'HSH',
    'hh': 'HH',
    'ss': 'SS',
    'sss': 'SSS',
    'single': 'S',
    'humbucker': 'HH',
    'humbuckers': 'HH',
    'single coil': 'S',
    'single-coil': 'S',
    'p90': 'P90',
}

# Бренды для распознавания
BRAND_KEYWORDS = {
    'fender': 'Fender',
    'gibson': 'Gibson',
    'ibanez': 'Ibanez',
    'prs': 'PRS',
    'squier': 'Squier',
    'epiphone': 'Epiphone',
    'yamaha': 'Yamaha',
    'g&l': 'G&L',
    'g and l': 'G&L',
    'harley benton': 'Harley Benton',
    'cort': 'Cort',
    'schecter': 'Schecter',
    'jackson': 'Jackson',
    'esp': 'ESP',
    'music man': 'Music Man',
    'rickenbacker': 'Rickenbacker',
}


def parse_guitar_title(title: str) -> dict:
    """
    Извлекает параметры гитары из названия.

    Args:
        title: Название гитары (например, "Fender Player Stratocaster HSS")

    Returns:
        dict с полями:
            - type: тип гитары (Stratocaster, Telecaster, Les Paul, etc.)
            - pickups: конфигурация датчиков (HSS, HH, S, etc.)
            - brand: бренд (Fender, Gibson, etc.)

    Примеры:
        >>> parse_guitar_title("Fender Player Stratocaster HSS")
        {'type': 'Stratocaster', 'pickups': 'HSS', 'brand': 'Fender'}

        >>> parse_guitar_title("Gibson Les Paul Studio")
        {'type': 'Les Paul', 'pickups': None, 'brand': 'Gibson'}
    """
    title_lower = title.lower()

    # Извлекаем бренд
    brand = None
    for keyword, value in BRAND_KEYWORDS.items():
        if keyword in title_lower:
            brand = value
            break

    # Извлекаем тип гитары
    # Сортируем ключи по длине (убывание) чтобы сначала искать более длинные совпадения
    # (например, "flying v" вместо "v")
    sorted_type_keywords = sorted(TYPE_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True)
    guitar_type = None
    for keyword, value in sorted_type_keywords:
        if keyword in title_lower:
            guitar_type = value
            break

    # Извлекаем датчики
    # Сортируем ключи по длине (убывание) чтобы сначала искать более длинные совпадения
    # (например, "single coil" вместо "single")
    sorted_pickups_keywords = sorted(PICKUPS_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True)
    pickups = None
    for keyword, value in sorted_pickups_keywords:
        if keyword in title_lower:
            pickups = value
            break

    return {
        'type': guitar_type,
        'pickups': pickups,
        'brand': brand
    }


def enrich_guitar_data(guitar: dict) -> dict:
    """
    Обогащает данные гитары, извлекая параметры из title.

    Args:
        guitar: Словарь с данными гитары (минимум title, price, etc.)

    Returns:
        Копия guitar с добавленными полями type, pickups, brand (если не были указаны)
    """
    result = guitar.copy()

    # Извлекаем данные из title только если поля не указаны явно
    if 'type' not in result or 'pickups' not in result or 'brand' not in result:
        parsed = parse_guitar_title(result.get('title', ''))

        if 'type' not in result:
            result['type'] = parsed['type']
        if 'pickups' not in result:
            result['pickups'] = parsed['pickups']
        if 'brand' not in result:
            result['brand'] = parsed['brand']

    # Добавляем default значения для condition и country если не указаны
    if 'condition' not in result:
        result['condition'] = 'New'  # по умолчанию считаем новым
    if 'country' not in result:
        result['country'] = ''  # неизвестная страна

    return result
