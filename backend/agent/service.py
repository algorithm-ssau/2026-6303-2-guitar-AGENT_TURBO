"""Сервис агента: точка входа для обработки пользовательских запросов.

Связывает полный пайплайн: detect_mode → LLM → search_reverb → rank_results.
Поддерживает callback on_status для отправки промежуточных статусов.
"""

import os
from typing import Callable, Optional

from backend.agent.llm_client import LLMClient
from backend.agent.mode_detector import detect_mode
from backend.agent.param_extractor import extract_params_from_llm_response
from backend.ranking.ranking import rank_results
from backend.search.search_reverb import search_reverb


def get_system_prompt() -> str:
    """Загружает системный промпт из файла AGENT_PROMPT.md"""
    prompt_path = os.path.join(os.path.dirname(__file__), "../../docs/AGENT_PROMPT.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Ты ИИ-агент по подбору гитар. ВЕРНИ СТРОГО JSON."


def get_consultation_prompt() -> str:
    """Загружает промпт для консультационного режима из CONSULTATION_PROMPT.md"""
    prompt_path = os.path.join(os.path.dirname(__file__), "../../docs/CONSULTATION_PROMPT.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Ты консультант по гитарам. Помогаешь понять, как параметры инструмента влияют на звук."


def create_llm_client() -> Optional[LLMClient]:
    """Создаёт LLMClient. Возвращает None если GROQ_API_KEY не задан."""
    try:
        return LLMClient()
    except (ValueError, Exception):
        return None


def interpret_query(
    text: str,
    llm_client=None,
    search_fn=None,
    on_status: Optional[Callable[[str], None]] = None,
) -> dict:
    """Обрабатывает запрос пользователя через полный пайплайн.

    Пайплайн:
    - Consultation: detect_mode → статус → LLM отвечает → return answer
    - Search: detect_mode → статус → LLM параметры → search → ranking → return results

    Args:
        text: Текстовый запрос пользователя
        llm_client: LLMClient для тестов (если None — создаётся через create_llm_client)
        search_fn: Функция поиска для тестов (если None — используется search_reverb)
        on_status: Callback для промежуточных статусов (если None — статусы не отправляются)

    Returns:
        dict с ключами mode и params/results (для поиска) или answer (для консультации)
    """
    # Определяем режим
    mode = detect_mode(text)
    if on_status:
        on_status("Определяю режим...")

    # Получаем LLM-клиент
    if llm_client is None:
        llm_client = create_llm_client()

    # Выбираем функцию поиска
    actual_search_fn = search_fn or search_reverb

    if mode == "consultation":
        return _handle_consultation(text, llm_client, on_status)
    else:
        return _handle_search(text, llm_client, actual_search_fn, on_status)


def _handle_consultation(
    text: str,
    llm_client: Optional[LLMClient],
    on_status: Optional[Callable[[str], None]],
) -> dict:
    """Обработка консультационного запроса."""
    if on_status:
        on_status("Формирую ответ...")

    # Fallback без LLM-клиента
    if llm_client is None:
        return {
            "mode": "consultation",
            "answer": "К сожалению, сервис временно недоступен (API ключ не настроен). "
                      "Попробуйте позже.",
        }

    try:
        prompt = get_consultation_prompt()
        answer = llm_client.ask(text, prompt)
        return {"mode": "consultation", "answer": answer}
    except Exception as e:
        return {
            "mode": "consultation",
            "answer": f"Извините, произошла ошибка обработки: {str(e)}",
        }


def _handle_search(
    text: str,
    llm_client: Optional[LLMClient],
    search_fn,
    on_status: Optional[Callable[[str], None]],
) -> dict:
    """Обработка поискового запроса."""
    # Генерация параметров поиска
    if on_status:
        on_status("Генерирую параметры поиска...")

    if llm_client is not None:
        try:
            params = llm_client.extract_search_params(text)
        except Exception:
            # Fallback: используем текст запроса как search_queries
            params = {"search_queries": [text], "price_min": None, "price_max": None}
    else:
        # Без API-ключа: используем текст запроса как search_queries
        params = {"search_queries": [text], "price_min": None, "price_max": None}

    # Поиск на Reverb
    if on_status:
        on_status("Ищу на Reverb...")

    results = search_fn(
        params.get("search_queries", []),
        params.get("price_min"),
        params.get("price_max"),
    )

    # Ранжирование результатов
    if on_status:
        on_status("Ранжирую результаты...")

    ranked = rank_results(results, {"budget_max": params.get("price_max")})

    return {"mode": "search", "results": ranked}
