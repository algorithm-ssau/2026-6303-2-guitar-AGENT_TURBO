"""
Модуль ранжирования результатов поиска гитар.

Отвечает за оценку и сортировку результатов поиска по релевантности
запросу пользователя на основе критериев из docs/RANKING.md.
"""

# Веса критериев ранжирования
WEIGHTS = {
    'budget': 0.30,
    'type': 0.25,
    'pickups': 0.20,
    'brand': 0.10,
    'condition': 0.10,
    'country': 0.05
}

# Премиум бренды
PREMIUM_BRANDS = ['fender', 'gibson', 'prs', 'ibanez', 'g&l', 'g and l']
# Бренды среднего сегмента
MID_BRANDS = ['squier', 'epiphone', 'yamaha']
# Бюджетные бренды
BUDGET_BRANDS = ['harley benton', 'cort', 'lag', 'farida']

# Страны производства и их scores
COUNTRY_SCORES = {
    'usa': 100,
    'japan': 95,
    'mexico': 80,
    'korea': 70,
    'china': 60,
    'indonesia': 70,
    'india': 60
}

# Состояния и их scores
CONDITION_SCORES = {
    'new': 100,
    'excellent': 80,
    'good': 60,
    'fair': 40
}

# Конфигурации датчиков
SINGLE_COIL_CONFIGS = ['s', 'ss', 'sss', 'single', 'single coil']
HUMBUCKER_CONFIGS = ['h', 'hh', 'humbucker']
MIXED_CONFIGS = ['hs', 'sh', 'hss', 'hsh']


def score_budget(result: dict, params: dict) -> float:
    """
    Оценивает соответствие цены бюджету пользователя.
    
    100 баллов: цена внутри запрошенного диапазона
    50 баллов: цена превышает бюджет не более чем на 20%
    0 баллов: цена превышает бюджет более чем на 20%
    """
    if 'budget_max' not in params or params['budget_max'] is None:
        # Если бюджет не указан — возвращаем нейтральный score
        return 70.0
    
    price = result.get('price', 0)
    budget_max = params['budget_max']
    
    if price <= budget_max:
        return 100.0
    elif price <= budget_max * 1.2:
        return 50.0
    else:
        return 0.0


def score_type(result: dict, params: dict) -> float:
    """
    Оценивает совпадение типа инструмента.
    
    100 баллов: точное совпадение
    60 баллов: похожий тип (superstrat вместо stratocaster)
    0 баллов: совершенно другой тип
    """
    if 'type' not in params or params['type'] is None:
        return 60.0  # нейтральный score если тип не указан
    
    requested_type = params['type'].lower()
    result_type = result.get('type', '').lower()
    
    # Точное совпадение
    if requested_type == result_type:
        return 100.0
    
    # Похожий тип (superstrat ~ stratocaster)
    similar_types = {
        'stratocaster': ['superstrat', 'strat'],
        'telecaster': ['tele'],
        'les paul': ['lp', 'lespaul'],
        'sg': ['sg'],
        'explorer': ['explorer'],
        'flying v': ['v', 'flying v']
    }
    
    for key, similar in similar_types.items():
        if requested_type == key and result_type in similar:
            return 60.0
        if requested_type in similar and result_type == key:
            return 60.0
    
    # Проверка на частичное совпадение строк
    if requested_type in result_type or result_type in requested_type:
        return 60.0
    
    return 0.0


def score_pickups(result: dict, params: dict) -> float:
    """
    Оценивает совпадение конфигурации датчиков.
    
    100 баллов: точное совпадение (SSS, HH, HSS, P90)
    70 баллов: похожий характер звука
    0 баллов: противоположный характер
    """
    if 'pickups' not in params or params['pickups'] is None:
        return 70.0  # нейтральный score если датчики не указаны
    
    requested_pickups = params['pickups'].lower()
    result_pickups = result.get('pickups', '').lower()
    
    # Точное совпадение
    if requested_pickups == result_pickups:
        return 100.0
    
    # Нормализация форматов
    req_normalized = requested_pickups.replace(' ', '').replace('-', '')
    res_normalized = result_pickups.replace(' ', '').replace('-', '')
    
    if req_normalized == res_normalized:
        return 100.0
    
    # Проверка на single coil
    if requested_pickups in SINGLE_COIL_CONFIGS:
        if result_pickups in SINGLE_COIL_CONFIGS:
            return 100.0
        elif result_pickups in MIXED_CONFIGS:
            return 70.0  # частично похоже
        elif result_pickups in HUMBUCKER_CONFIGS:
            return 0.0  # противоположный характер
    
    # Проверка на humbucker
    if requested_pickups in HUMBUCKER_CONFIGS:
        if result_pickups in HUMBUCKER_CONFIGS:
            return 100.0
        elif result_pickups in MIXED_CONFIGS:
            return 70.0  # частично похоже
        elif result_pickups in SINGLE_COIL_CONFIGS:
            return 0.0  # противоположный характер
    
    # Проверка на mixed
    if requested_pickups in MIXED_CONFIGS:
        if result_pickups in MIXED_CONFIGS:
            return 100.0
        return 70.0  # частично похоже на что-то
    
    # P90 — особый тип single coil
    if 'p90' in requested_pickups or 'p90' in result_pickups:
        if 'p90' in requested_pickups and 'p90' in result_pickups:
            return 100.0
        if 'p90' in requested_pickups and result_pickups in SINGLE_COIL_CONFIGS:
            return 70.0
        if 'p90' in result_pickups and requested_pickups in SINGLE_COIL_CONFIGS:
            return 70.0
    
    return 50.0  # нейтральный score если не удалось определить


def score_brand(result: dict, params: dict) -> float:
    """
    Оценивает бренд гитары.
    
    100 баллов: запрошенный бренд
    80 баллов: премиум бренд (Fender, Gibson, PRS, Ibanez)
    60 баллов: средний сегмент (Squier, Epiphone, Yamaha)
    40 баллов: бюджетный бренд
    """
    result_brand = result.get('brand', '').lower()
    
    # Если бренд указан в параметрах — ищем точное совпадение
    if 'brand' in params and params['brand'] is not None:
        requested_brand = params['brand'].lower()
        if requested_brand == result_brand:
            return 100.0
        # Частичное совпадение названия бренда
        if requested_brand in result_brand or result_brand in requested_brand:
            return 80.0
    
    # Если бренд не указан — оцениваем по категории
    for premium in PREMIUM_BRANDS:
        if premium in result_brand:
            return 80.0
    
    for mid in MID_BRANDS:
        if mid in result_brand:
            return 60.0
    
    for budget in BUDGET_BRANDS:
        if budget in result_brand:
            return 40.0
    
    return 50.0  # неизвестный бренд — нейтральный score


def score_condition(result: dict, params: dict) -> float:
    """
    Оценивает состояние инструмента.
    
    100 баллов: new condition
    80 баллов: excellent condition
    60 баллов: good condition
    40 баллов: fair condition
    """
    result_condition = result.get('condition', '').lower()
    
    # Если состояние указано в параметрах — предпочитаем его
    if 'condition' in params and params['condition'] is not None:
        requested_condition = params['condition'].lower()
        if requested_condition == result_condition:
            return 100.0
    
    # Оцениваем по стандартной шкале
    for condition, score in CONDITION_SCORES.items():
        if condition in result_condition:
            return score
    
    # Проверка на русские варианты написания
    if 'нов' in result_condition or 'new' in result_condition:
        return 100.0
    if 'отличн' in result_condition or 'excellent' in result_condition:
        return 80.0
    if 'хорош' in result_condition or 'good' in result_condition:
        return 60.0
    if 'удовл' in result_condition or 'fair' in result_condition:
        return 40.0
    
    return 60.0  # по умолчанию good condition


def score_country(result: dict, params: dict) -> float:
    """
    Оценивает страну производства.
    
    Приоритеты:
    1. 100 баллов: точное совпадение с запрошенной страной (наивысший приоритет)
    2. Далее по шкале: USA (100), Japan (95), Mexico (80), Korea (70), China (60)
    """
    result_country = result.get('country', '').lower()
    
    # ПЕРВЫЙ ПРИОРИТЕТ: если страна указана в параметрах — ищем точное совпадение
    if 'country' in params and params['country'] is not None:
        requested_country = params['country'].lower()
        # Точное совпадение с запросом пользователя — всегда 100 баллов
        if requested_country == result_country:
            return 100.0
        # Частичное совпадение (например 'usa' в 'united states')
        if requested_country in result_country or result_country in requested_country:
            return 100.0
    
    # ВТОРОЙ ПРИОРИТЕТ: оцениваем по стандартной шкале
    for country, score in COUNTRY_SCORES.items():
        if country in result_country:
            return score
    
    return 60.0  # неизвестная страна — нейтральный score


def calculate_total_score(result: dict, params: dict) -> float:
    """
    Вычисляет итоговый score для результата.
    
    Формула:
    Итоговый_score = (бюджет_score × 0.30) + (тип_score × 0.25) +
                     (датчики_score × 0.20) + (бренд_score × 0.10) +
                     (состояние_score × 0.10) + (страна_score × 0.05)
    """
    budget_score = score_budget(result, params)
    type_score = score_type(result, params)
    pickups_score = score_pickups(result, params)
    brand_score = score_brand(result, params)
    condition_score = score_condition(result, params)
    country_score = score_country(result, params)
    
    total_score = (
        budget_score * WEIGHTS['budget'] +
        type_score * WEIGHTS['type'] +
        pickups_score * WEIGHTS['pickups'] +
        brand_score * WEIGHTS['brand'] +
        condition_score * WEIGHTS['condition'] +
        country_score * WEIGHTS['country']
    )
    
    return round(total_score, 2)


def rank_results(results: list, params: dict) -> list:
    """
    Ранжирует результаты поиска по релевантности.

    Args:
        results: Список результатов от Reverb (сырые данные).
        params: Параметры поиска из LLM (бюджет, тип, датчики и т.д.)

    Returns:
        Топ-5 отсортированных результатов с добавленным полем 'score'

    Критерии оценки (веса):
        - Бюджет: 30%
        - Тип инструмента: 25%
        - Конфигурация датчиков: 20%
        - Бренд: 10%
        - Состояние: 10%
        - Страна производства: 5%
    """
    if not results:
        return []
    
    # Вычисляем score для каждого результата
    scored_results = []
    for result in results:
        result_copy = result.copy()  # не модифицируем оригинал
        total_score = calculate_total_score(result_copy, params)
        result_copy['score'] = total_score
        scored_results.append(result_copy)
    
    # Сортируем по убыванию score
    scored_results.sort(key=lambda x: x['score'], reverse=True)
    
    # Возвращаем топ-5
    return scored_results[:5]
