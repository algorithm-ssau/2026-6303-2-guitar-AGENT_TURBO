"""
Модуль ранжирования результатов поиска гитар.

Поддерживает два режима:
- Упрощённый: бюджет (55%) + совпадение названия (45%) — когда нет фильтров кроме query/budget
- Расширенный: бюджет + тип + датчики + бренд + sound/style + название
"""


def _keyword_score(title: str, strong_keywords: list[str], soft_keywords: list[str]) -> float:
    """Возвращает score по эвристикам ключевых слов в title."""
    strong_hits = sum(1 for keyword in strong_keywords if keyword in title)
    soft_hits = sum(1 for keyword in soft_keywords if keyword in title)

    if strong_hits >= 2:
        return 100.0
    if strong_hits == 1:
        return 85.0
    if soft_hits >= 2:
        return 70.0
    if soft_hits == 1:
        return 60.0
    return 25.0


def score_budget(result: dict, params: dict) -> float:
    """
    Оценивает соответствие цены бюджету пользователя.

    100 баллов: цена внутри бюджета (≤ price_max)
    50 баллов: превышает до 20%
    0 баллов: превышает более 20%
    50 баллов: бюджет не указан
    """
    price = result.get('price', 0)
    price_max = params.get('budget_max') or params.get('price_max')

    if price_max is None:
        return 50.0  # нейтральный score если бюджет не указан

    if price <= price_max:
        return 100.0
    elif price <= price_max * 1.2:
        return 50.0
    else:
        return 0.0


def score_title(result: dict, params: dict) -> float:
    """
    Оценивает совпадение названия гитары с поисковым запросом.

    100 баллов: полное совпадение фразы
    70 баллов: 2+ слова из запроса в названии
    40 баллов: 1 слово из запроса в названии
    0 баллов: нет совпадений
    0 баллов: search_queries не указан
    """
    search_queries = params.get('search_queries')

    if not search_queries:
        return 0.0  # нейтральный score если запрос не указан

    title = result.get('title', '').lower()

    # Нормализуем search_queries — это может быть строка или список
    if isinstance(search_queries, str):
        queries = search_queries.lower().split()
        queries_str = search_queries.lower()
    else:
        queries = [q.lower() for q in search_queries]
        queries_str = ' '.join(queries)

    # Полное совпадение фразы
    if queries_str in title or title in queries_str:
        return 100.0

    # Считаем количество совпавших слов
    match_count = 0
    for query in queries:
        if query in title:
            match_count += 1

    if match_count >= 2:
        return 70.0
    elif match_count == 1:
        return 40.0
    else:
        return 0.0


def score_type(result: dict, params: dict) -> float:
    """
    Оценивает совпадение типа гитары.

    100 баллов: точное совпадение типа
    60 баллов: похожий тип
    0 баллов: несовпадение
    50 баллов: тип не указан в params
    """
    requested_type = params.get('type')

    if not requested_type:
        return 50.0  # нейтральный score если тип не указан

    title = result.get('title', '').lower()
    requested_type_lower = requested_type.lower()

    # Точное совпадение типа в названии
    if requested_type_lower in title:
        return 100.0

    # Маппинг похожих типов
    similar_types = {
        'stratocaster': ['strat', 'superstrat'],
        'telecaster': ['tele'],
        'les paul': ['lp'],
        'sg': ['sg'],
        'superstrat': ['stratocaster', 'strat'],
    }

    # Проверяем похожие типы
    for key, similar in similar_types.items():
        if requested_type_lower == key:
            for sim in similar:
                if sim in title:
                    return 60.0

    return 0.0


def score_pickups(result: dict, params: dict) -> float:
    """
    Оценивает совпадение конфигурации датчиков.

    100 баллов: точное совпадение
    70 баллов: похожий звук
    30 баллов: противоположный характер
    50 баллов: датчики не указаны
    """
    requested_pickups = params.get('pickups')

    if not requested_pickups:
        return 50.0  # нейтральный score если датчики не указаны

    title = result.get('title', '').lower()
    requested_pickups_lower = requested_pickups.lower()

    # Точное совпадение конфигурации
    if requested_pickups_lower in title:
        return 100.0

    # Маппинг похожих конфигураций
    similar_pickups = {
        'sss': ['single', 'ss'],
        'hh': ['humbucker', 'h'],
        'hss': ['hs', 'ss'],
        'p90': ['p-90'],
    }

    # Проверяем похожие конфигурации
    for key, similar in similar_pickups.items():
        if requested_pickups_lower == key:
            for sim in similar:
                if sim in title:
                    return 70.0

    # Проверяем противоположный характер
    if requested_pickups_lower in ['sss', 'single'] and 'hh' in title:
        return 30.0
    if requested_pickups_lower == 'hh' and 'sss' in title:
        return 30.0

    return 0.0


def score_brand(result: dict, params: dict) -> float:
    """
    Оценивает совпадение бренда.

    100 баллов: запрошенный бренд точно совпал
    80 баллов: премиум бренд (Fender, Gibson, PRS, Ibanez)
    60 баллов: средний сегмент (Squier, Epiphone, Yamaha)
    40 баллов: бюджетный/неизвестный бренд
    50 баллов: бренд не указан
    """
    requested_brand = params.get('brand')

    if not requested_brand:
        return 50.0  # нейтральный score если бренд не указан

    title = result.get('title', '').lower()
    requested_brand_lower = requested_brand.lower()

    # Точное совпадение бренда
    if requested_brand_lower in title:
        return 100.0

    # Определяем сегмент бренда по названию
    premium_brands = ['fender', 'gibson', 'prs', 'ibanez']
    mid_brands = ['squier', 'epiphone', 'yamaha', 'g&l']

    for brand in premium_brands:
        if brand in title:
            return 80.0

    for brand in mid_brands:
        if brand in title:
            return 60.0

    return 40.0


def score_sound(result: dict, params: dict) -> float:
    """Оценивает соответствие характера звука по эвристикам названия."""
    requested_sound = str(params.get('sound') or '').strip().lower()
    if not requested_sound:
        return 50.0

    title = result.get('title', '').lower()
    sound_profiles = {
        'bright': {
            'strong': ['telecaster', 'stratocaster', 'single-coil', 'single coil', 'sss'],
            'soft': ['tele', 'strat', 'maple', 'ash', 'twang'],
        },
        'warm': {
            'strong': ['les paul', 'semi-hollow', 'semi hollow', 'humbucker', 'hh'],
            'soft': ['mahogany', 'p90', 'es-335', 'jazzmaster'],
        },
        'fat': {
            'strong': ['les paul', 'humbucker', 'hh', 'baritone'],
            'soft': ['mahogany', 'p90', 'sg'],
        },
        'clean': {
            'strong': ['stratocaster', 'telecaster', 'single-coil', 'single coil'],
            'soft': ['strat', 'tele', 'semi-hollow', 'semi hollow'],
        },
    }

    profile = sound_profiles.get(requested_sound)
    if not profile:
        return 50.0

    return _keyword_score(title, profile['strong'], profile['soft'])


def score_style(result: dict, params: dict) -> float:
    """Оценивает соответствие музыкальному стилю по эвристикам названия."""
    requested_style = str(params.get('style') or '').strip().lower()
    if not requested_style:
        return 50.0

    title = result.get('title', '').lower()
    style_profiles = {
        'metal': {
            'strong': ['7-string', '7 string', 'emg', 'active', 'floyd rose'],
            'soft': ['ibanez rg', 'jackson', 'esp', 'ltd', 'schecter'],
        },
        'jazz': {
            'strong': ['hollow body', 'archtop', 'semi-hollow', 'semi hollow'],
            'soft': ['es-335', 'casino', 'jazzmaster'],
        },
        'blues': {
            'strong': ['stratocaster', 'telecaster', 'semi-hollow', 'semi hollow'],
            'soft': ['strat', 'tele', 'p90', 'es-335'],
        },
        'rock': {
            'strong': ['les paul', 'sg', 'humbucker'],
            'soft': ['telecaster', 'stratocaster', 'prs'],
        },
    }

    profile = style_profiles.get(requested_style)
    if not profile:
        return 50.0

    return _keyword_score(title, profile['strong'], profile['soft'])


def calculate_total_score(result: dict, params: dict, use_full_formula: bool = True) -> float:
    """
    Вычисляет итоговый score для результата.

    Args:
        result: Данные результата поиска
        params: Параметры поиска
        use_full_formula: Если True — полная формула, иначе — упрощённая

    Упрощённая: (бюджет × 0.55) + (название × 0.45)
    Расширенная: бюджет(25%) + тип(20%) + датчики(15%) + бренд(10%) + sound(10%) + style(10%) + название(10%)
    """
    budget_score = score_budget(result, params)
    title_score = score_title(result, params)

    if not use_full_formula:
        # Упрощённая формула — когда нет type/pickups/brand
        total_score = (budget_score * 0.55) + (title_score * 0.45)
    else:
        # Расширенная формула — когда есть дополнительные фильтры
        type_score = score_type(result, params)
        pickups_score = score_pickups(result, params)
        brand_score = score_brand(result, params)
        sound_score = score_sound(result, params)
        style_score = score_style(result, params)

        total_score = (
            (budget_score * 0.25) +
            (type_score * 0.20) +
            (pickups_score * 0.15) +
            (brand_score * 0.10) +
            (sound_score * 0.10) +
            (style_score * 0.10) +
            (title_score * 0.10)
        )

    return round(total_score, 2)


def rank_results(results: list, params: dict) -> list:
    """
    Ранжирует результаты поиска по релевантности.

    Args:
        results: Список объявлений с Reverb
        params: Параметры поиска (budget_max, search_queries, type, pickups, brand, sound, style)

    Returns:
        Топ-5 результатов БЕЗ полей score/_score

    Автоматически выбирает формулу:
        - Если есть type/pickups/brand/sound/style — расширенная формула
        - Иначе — упрощённая (budget + title)
    """
    if not results:
        return []

    # Расширенная формула включается при любом дополнительном фильтре.
    has_full_params = any(params.get(key) is not None for key in ['type', 'pickups', 'brand', 'sound', 'style'])

    # Вычисляем score для каждого результата
    scored_results = []
    for result in results:
        result_copy = result.copy()
        total_score = calculate_total_score(result_copy, params, has_full_params)
        scored_results.append((result_copy, total_score))

    # Сортируем по убыванию score
    scored_results.sort(key=lambda x: x[1], reverse=True)

    # Возвращаем топ-5 БЕЗ score/_score
    final_results = [result for result, score in scored_results[:5]]

    # Очищаем поля score/_score если они вдруг попали
    for r in final_results:
        r.pop('score', None)
        r.pop('_score', None)

    return final_results
