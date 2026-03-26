"""
Модуль ранжирования результатов поиска гитар.
Упрощённая версия: бюджет (55%) + совпадение названия (45%)
"""


def score_budget(result: dict, params: dict) -> float:
    """
    Оценивает соответствие цены бюджету пользователя.
    
    100 баллов: цена внутри бюджета (≤ price_max)
    50 баллов: превышает до 20%
    0 баллов: превышает более 20%
    50 баллов: бюджет не указан
    """
    price = result.get('price', 0)
    price_max = params.get('price_max')
    
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
    else:
        queries = [q.lower() for q in search_queries]
    
    # Полное совпадение фразы
    if search_queries.lower() in title or title in search_queries.lower():
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


def calculate_total_score(result: dict, params: dict) -> float:
    """
    Вычисляет итоговый score для результата.
    
    Формула: (бюджет_score × 0.55) + (название_score × 0.45)
    """
    budget_score = score_budget(result, params)
    title_score = score_title(result, params)
    
    total_score = (budget_score * 0.55) + (title_score * 0.45)
    
    return round(total_score, 2)


def rank_results(results: list, params: dict) -> list:
    """
    Ранжирует результаты поиска по релевантности.
    
    Args:
        results: Список объявлений с Reverb
        params: Параметры поиска (price_min, price_max, search_queries)
    
    Returns:
        Топ-5 результатов БЕЗ поля _score
    
    Формула: бюджет (55%) + название (45%)
    """
    if not results:
        return []
    
    # Вычисляем score для каждого результата
    scored_results = []
    for result in results:
        result_copy = result.copy()
        total_score = calculate_total_score(result_copy, params)
        # НЕ добавляем _score в результат!
        scored_results.append((result_copy, total_score))
    
    # Сортируем по убыванию score
    scored_results.sort(key=lambda x: x[1], reverse=True)
    
    # Возвращаем топ-5 БЕЗ _score
    return [result for result, score in scored_results[:5]]
