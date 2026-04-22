# filepath: backend/agent/params_echo.py
import re

def parse_query_simple(query: str) -> dict:
    q = query.lower()
    params = {
        "price_min": None,
        "price_max": None,
        "type": None,
        "brand": None,
        "tags":[]
    }

    # 1. Бюджет: Рубли (в приоритете, т.к. требует конвертации)
    rub_match = re.search(r"(\d+)\s*(тыс|000)?\s*руб", q)
    if rub_match:
        val = int(rub_match.group(1))
        # Если есть множитель (тыс или 000), умножаем на 1000
        if rub_match.group(2) in ["тыс", "000"]:
            val *= 1000
        params["price_max"] = val // 100
    else:
        # 2. Бюджет: Диапазон
        range_match = re.search(r"(\d+)\s*[–-]\s*(\d+)", q)
        if range_match:
            params["price_min"] = int(range_match.group(1))
            params["price_max"] = int(range_match.group(2))
        else:
            # 3. Бюджет: Максимум (до / up to / <=)
            up_to_match = re.search(r"(?:до|up to|<=?)\s*\$?(\d+)", q)
            if up_to_match:
                params["price_max"] = int(up_to_match.group(1))
            
            # 4. Бюджет: Минимум (от / from / >=)
            from_match = re.search(r"(?:от|from|>=?)\s*\$?(\d+)", q)
            if from_match:
                params["price_min"] = int(from_match.group(1))

    # Тип гитары
    if re.search(r"\b(strat|стратокастер|stratocaster)\b", q): 
        params["type"] = "stratocaster"
    elif re.search(r"\b(tele|телекастер|теле|telecaster)\b", q): 
        params["type"] = "telecaster"
    elif re.search(r"\b(lp|лес пол|les paul)\b", q): 
        params["type"] = "les paul"
    elif re.search(r"\b(акустик|акустика|acoustic)\b", q): 
        params["type"] = "acoustic"
    elif re.search(r"\b(бас|bass|бас-гитара)\b", q): 
        params["type"] = "bass"

    # Бренд
    brand_match = re.search(r"\b(fender|gibson|ibanez|prs|yamaha|taylor|martin|squier|epiphone)\b", q)
    if brand_match:
        params["brand"] = brand_match.group(1)

    # Теги стилей
    tag_map = {
        "джаз": "jazz", "jazz": "jazz",
        "блюз": "blues", "blues": "blues",
        "метал": "metal", "metal": "metal",
        "фанк": "funk", "funk": "funk",
        "кантри": "country", "country": "country"
    }
    tags =[]
    for kw, tag in tag_map.items():
        if re.search(rf"\b{kw}\b", q) and tag not in tags:
            tags.append(tag)
    params["tags"] = tags

    return params

def format_params_for_display(params: dict) -> dict:
    # Форматирование типа
    t = params.get("type")
    t_formatted = None
    if t == "stratocaster": t_formatted = "Stratocaster"
    elif t == "telecaster": t_formatted = "Telecaster"
    elif t == "les paul": t_formatted = "Les Paul"
    elif t == "acoustic": t_formatted = "Acoustic"
    elif t == "bass": t_formatted = "Bass"
    elif t: t_formatted = t.title()

    # Форматирование бренда
    b = params.get("brand")
    b_formatted = b.title() if b else None
    if b == "prs": b_formatted = "PRS"

    # Форматирование бюджета
    p_min = params.get("price_min")
    p_max = params.get("price_max")
    budget = None
    if p_min is not None and p_max is not None:
        budget = f"${p_min}–${p_max}"
    elif p_max is not None:
        budget = f"≤ ${p_max}"
    elif p_min is not None:
        budget = f"≥ ${p_min}"

    return {
        "type": t_formatted,
        "budget": budget,
        "brand": b_formatted,
        "tags": params.get("tags",[])
    }