"""Сервис агента: точка входа для обработки пользовательских запросов.

Связывает полный пайплайн: detect_mode → LLM → search_reverb → rank_results.
Поддерживает callback on_status для отправки промежуточных статусов.
"""

import os
from typing import Callable, Optional

from backend.agent.llm_client import LLMClient
from backend.agent.mode_detector import detect_mode, OFF_TOPIC_ANSWER
from backend.agent.param_extractor import extract_params_from_llm_response
from backend.agent.clarification import check_needs_clarification
from backend.ranking.ranking import rank_results
from backend.search.search_reverb import search_reverb
from backend.history.service import get_session_messages
from backend.utils.logger import get_logger

logger = get_logger("agent.service")


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


def _get_last_search_query(session_id: Optional[int]) -> Optional[str]:
    """Возвращает user_query последнего поискового запроса в сессии (или None)."""
    if not session_id:
        return None
    try:
        items = get_session_messages(session_id)
        for item in reversed(items):
            if item.get("mode") == "search":
                return item.get("user_query")
    except Exception as e:
        logger.error("Ошибка поиска предыдущего запроса: %s", e)
    return None


def interpret_query(
    text: str,
    llm_client=None,
    search_fn=None,
    on_status: Optional[Callable[[str], None]] = None,
    session_id: Optional[int] = None,
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
    # Проверяем наличие предыдущего поиска в сессии (для контекстного пере-поиска)
    last_search_query = _get_last_search_query(session_id)

    # Определяем режим
    try:
        mode = detect_mode(text, has_previous_search=last_search_query is not None)
    except Exception as e:
        logger.error("Ошибка detect_mode, fallback на consultation: %s", e)
        mode = "consultation"
    if on_status:
        on_status("Определяю режим...")

    # Off-topic — сразу возвращаем отказ, без вызова LLM
    if mode == "off_topic":
        return {"mode": "consultation", "answer": OFF_TOPIC_ANSWER}

    # Получаем LLM-клиент
    if llm_client is None:
        llm_client = create_llm_client()

    # Выбираем функцию поиска
    actual_search_fn = search_fn or search_reverb

    from backend.agent.context_manager import build_context
    system_prompt = get_consultation_prompt() if mode == "consultation" else get_system_prompt()
    history = build_context(session_id, system_prompt, text, llm_client)

    if mode == "consultation":
        return _handle_consultation(text, llm_client, on_status, history)
    else:
        # Проверяем: это пере-поиск или новый запрос?
        # Если без контекста сессии режим был бы consultation — значит пере-поиск
        is_research = (
            last_search_query
            and detect_mode(text, has_previous_search=False) != "search"
        )
        search_text = last_search_query if is_research else text
        if is_research:
            logger.info("Пере-поиск: используем запрос из истории: %s", search_text)
        return _handle_search(search_text, llm_client, actual_search_fn, on_status)


def _handle_consultation(
    text: str,
    llm_client: Optional[LLMClient],
    on_status: Optional[Callable[[str], None]],
    history: list = None,
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
        answer = llm_client.ask(text, prompt, history=history)
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

    # Проверяем, нужно ли задать уточняющий вопрос
    clarification_question = check_needs_clarification(params)
    if clarification_question:
        return {"mode": "clarification", "question": clarification_question}

    # Поиск на Reverb
    if on_status:
        on_status("Ищу на Reverb...")

    try:
        results = search_fn(
            params.get("search_queries", []),
            params.get("price_min"),
            params.get("price_max"),
        )
    except Exception as e:
        logger.error("Ошибка search_reverb: %s", e)
        return {
            "mode": "search",
            "results": [],
            "error": "Не удалось выполнить поиск. Попробуйте позже.",
        }

    # Ранжирование результатов
    if on_status:
        on_status("Ранжирую результаты...")

    try:
        rank_params = {
            "budget_max": params.get("price_max"),
            "search_queries": params.get("search_queries", []),
            "type": params.get("type"),
            "pickups": params.get("pickups"),
            "brand": params.get("brand"),
        }
        ranked = rank_results(results, rank_params)
    except Exception as e:
        logger.error("Ошибка rank_results, возвращаю неранжированные: %s", e)
        ranked = results[:5]

    return {"mode": "search", "results": ranked}
