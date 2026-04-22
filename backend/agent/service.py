"""Сервис агента: точка входа для обработки пользовательских запросов.

Связывает полный пайплайн: detect_mode → LLM → search_reverb → rank_results.
Поддерживает callback on_status для отправки промежуточных статусов.
"""

import os
import re
from typing import Callable, Optional

from backend.agent.llm_client import LLMClient
from backend.agent.clarification import _is_no_preference
from backend.agent.mode_detector import detect_mode, OFF_TOPIC_ANSWER
from backend.agent.clarification import CLARIFICATION_QUESTIONS, check_needs_clarification
from backend.ranking.ranking import rank_results
from backend.search.search_reverb import search_reverb
from backend.history.service import get_session_messages, get_session_state, save_session_state
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


def _get_last_search_context_query(session_id: Optional[int]) -> Optional[str]:
    """Возвращает последний запрос из поискового контекста сессии."""
    if not session_id:
        return None
    try:
        items = get_session_messages(session_id)
        for item in reversed(items):
            if item.get("mode") in {"search", "clarification"}:
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
    last_search_query = _get_last_search_context_query(session_id)

    # Off-topic — жёсткая защита до LLM
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

    current_state = get_session_state(session_id) if session_id else {}
    router_history = _build_router_history(session_id)
    route_plan = _classify_query(
        text,
        llm_client,
        router_history,
        last_search_query is not None,
        current_state,
    )
    merged_state = _merge_search_state(current_state, route_plan.get("search_params"), route_plan.get("intent"))
    merged_state = _apply_no_preference_reply(text, merged_state)
    merged_state = _finalize_search_state(merged_state)
    if route_plan["intent"] == "consultation" and _should_resume_search(text, current_state, merged_state):
        route_plan = {**route_plan, "intent": "search", "consultation_answer": "", "should_offer_search": False}
    if session_id:
        save_session_state(session_id, merged_state)

    if route_plan["intent"] == "consultation":
        from backend.agent.context_manager import build_context
        history = build_context(session_id, get_consultation_prompt(), text, llm_client)
        if route_plan.get("consultation_answer"):
            answer = _sanitize_consultation_answer(route_plan["consultation_answer"])
            answer = _maybe_append_search_offer(answer, route_plan.get("should_offer_search", False))
            return {"mode": "consultation", "answer": answer}
        return _handle_consultation(
            text,
            llm_client,
            on_status,
            history,
            should_offer_search=route_plan.get("should_offer_search", False),
        )

    params = _state_to_search_params(merged_state)
    if not merged_state.get("ready_for_search"):
        merged_state["last_clarification_target"] = _clarification_target_from_missing_fields(merged_state.get("missing_fields", []))
        if session_id:
            save_session_state(session_id, merged_state)
        question = _question_from_missing_fields(merged_state.get("missing_fields", []), params)
        return {"mode": "clarification", "question": question}

    from backend.agent.context_manager import build_context
    history = build_context(session_id, get_system_prompt(), text, llm_client)
    return _handle_search(
        text,
        llm_client,
        actual_search_fn,
        on_status,
        history,
        initial_params=params,
    )


def _handle_consultation(
    text: str,
    llm_client: Optional[LLMClient],
    on_status: Optional[Callable[[str], None]],
    history: list = None,
    should_offer_search: bool = False,
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
        answer = _ask_consultation_llm(llm_client, text, prompt, history)
        answer = _sanitize_consultation_answer(answer)
        answer = _maybe_append_search_offer(answer, should_offer_search)
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
    history: Optional[list] = None,
    initial_params: Optional[dict] = None,
) -> dict:
    """Обработка поискового запроса."""
    # Генерация параметров поиска
    if on_status:
        on_status("Генерирую параметры поиска...")

    if initial_params is not None:
        params = initial_params
    elif llm_client is not None:
        try:
            params = llm_client.extract_search_params(text, history=history)
        except Exception:
            # Fallback: используем текст запроса как search_queries
            params = {"search_queries": [text], "price_min": None, "price_max": None}
    else:
        # Без API-ключа: используем текст запроса как search_queries
        params = {"search_queries": [text], "price_min": None, "price_max": None}

    # Если params пришли из уже нормализованного session state, второй раз не уходим в clarification.
    if initial_params is None:
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
        if not results:
            relaxed_queries = _build_relaxed_queries(params)
            if relaxed_queries:
                results = search_fn(
                    relaxed_queries,
                    params.get("price_min"),
                    params.get("price_max"),
                )
                if results:
                    params = {**params, "search_queries": relaxed_queries}
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
            "sound": params.get("sound"),
            "style": params.get("style"),
        }
        ranked = rank_results(results, rank_params)
    except Exception as e:
        logger.error("Ошибка rank_results, возвращаю неранжированные: %s", e)
        ranked = results[:5]

    return {"mode": "search", "results": ranked}


def _ask_consultation_llm(
    llm_client: LLMClient,
    text: str,
    prompt: str,
    history: Optional[list],
) -> str:
    """Вызывает LLM с history, но совместим со старыми сигнатурами ask()."""
    try:
        return llm_client.ask(text, prompt, history=history)
    except TypeError:
        return llm_client.ask(text, prompt)


def _sanitize_consultation_answer(answer: str) -> str:
    """Блокирует ответы консультации, похожие на каталог или ссылки."""
    text = (answer or "").strip()
    if not text:
        return text

    if _looks_like_catalog_content(text):
        return (
            "Сейчас это выглядит как запрос на подбор, а не консультацию. "
            "Чтобы показать только реальные варианты из каталога со ссылками, "
            "напишите тип гитары и бюджет, например: `Stratocaster до 1200$`."
        )

    return text


def _looks_like_catalog_content(text: str) -> bool:
    """Определяет, что LLM начал перечислять товары, магазины или ссылки."""
    lowered = text.lower()

    if re.search(r"https?://|www\.|\b[a-z0-9-]+\.(com|ru|net|org)\b", lowered):
        return True

    if re.search(r"\b(reverb|amazon|sweetwater|guitarcenter|musician'?s friend)\b", lowered):
        return True

    if "ссылка на пример" in lowered or "примеры телекастеров" in lowered:
        return True

    branded_models = re.findall(
        r"\b(Fender|Squier|Gibson|Epiphone|Ibanez|Jackson|PRS|Yamaha|ESP|Schecter|Gretsch|Charvel|Cort)\b(?:\s+[A-Z0-9][A-Za-z0-9'\-]+){1,4}",
        text,
    )
    return len(branded_models) >= 2


def _maybe_append_search_offer(answer: str, should_offer_search: bool) -> str:
    """Добавляет вариативное предложение перейти к реальным Reverb-вариантам."""
    if not should_offer_search:
        return answer

    offers = [
        "Если хотите, могу подобрать конкретные варианты с Reverb и показать ссылки.",
        "Если хотите, дальше покажу реальные варианты с Reverb со ссылками.",
        "Если хотите, могу сразу перейти к подбору на Reverb и показать конкретные объявления.",
        "Если хотите, подберу реальные варианты на Reverb и дам прямые ссылки на объявления.",
    ]
    index = sum(ord(char) for char in answer) % len(offers)
    suffix = offers[index]
    return f"{answer.rstrip()}\n\n{suffix}" if answer.strip() else suffix


def _build_router_history(session_id: Optional[int]) -> list:
    """Готовит компактную историю диалога для LLM-router."""
    if not session_id:
        return []

    try:
        items = get_session_messages(session_id)
    except Exception as e:
        logger.error("Ошибка чтения истории для router: %s", e)
        return []

    history = []
    for item in items[-6:]:
        history.append({"role": "user", "content": item.get("user_query", "")})
        if item.get("mode") == "search" and item.get("results"):
            titles = [result.get("title", "") for result in item.get("results", [])[:3]]
            assistant = "Найдены варианты на Reverb: " + ", ".join(filter(None, titles))
        else:
            assistant = item.get("answer") or ""
        history.append({"role": "assistant", "content": assistant})

    return history


def _classify_query(
    text: str,
    llm_client: Optional[LLMClient],
    history: list,
    has_previous_search: bool,
    current_state: dict,
) -> dict:
    """Определяет сценарий: search, clarification или consultation."""
    route_plan = None

    if llm_client is not None:
        try:
            candidate = llm_client.classify_and_plan_query(text, history=history, current_state=current_state)
            route_plan = _normalize_route_plan(candidate)
        except Exception as e:
            logger.error("Ошибка classify_and_plan_query: %s", e)

    if route_plan is not None:
        return route_plan

    return _fallback_route_plan(text, llm_client, history, has_previous_search, current_state)


def _normalize_route_plan(candidate: object) -> Optional[dict]:
    """Нормализует ответ router-LLM и отбрасывает невалидные структуры."""
    if not isinstance(candidate, dict):
        return None

    intent = candidate.get("intent")
    if intent not in {"search", "consultation"}:
        return None

    missing_fields = candidate.get("missing_fields")
    if not isinstance(missing_fields, list):
        missing_fields = []
    missing_fields = [field for field in missing_fields if field in {"budget", "type"}]

    enough_for_search = bool(candidate.get("enough_for_search"))
    if missing_fields:
        enough_for_search = False

    search_params = candidate.get("search_params")
    if not isinstance(search_params, dict):
        search_params = None

    consultation_answer = candidate.get("consultation_answer")
    if not isinstance(consultation_answer, str):
        consultation_answer = ""

    return {
        "intent": intent,
        "enough_for_search": enough_for_search,
        "missing_fields": missing_fields,
        "search_params": search_params,
        "consultation_answer": consultation_answer,
        "should_offer_search": bool(candidate.get("should_offer_search")),
    }


def _fallback_route_plan(
    text: str,
    llm_client: Optional[LLMClient],
    history: list,
    has_previous_search: bool,
    current_state: dict,
) -> dict:
    """Fallback, если router-LLM недоступен или вернул мусор."""
    mode = detect_mode(text, has_previous_search=has_previous_search)
    if current_state.get("ready_for_search") and _looks_like_followup_search_request(text):
        mode = "search"
    if mode == "consultation":
        return {
            "intent": "consultation",
            "enough_for_search": False,
            "missing_fields": [],
            "search_params": None,
            "consultation_answer": "",
            "should_offer_search": False,
        }

    params = None
    if llm_client is not None:
        try:
            params = llm_client.extract_search_params(text, history=history)
        except Exception:
            params = None

    if not isinstance(params, dict):
        params = {"search_queries": [text], "price_min": None, "price_max": None}

    missing_fields = _infer_missing_fields(params)
    return {
        "intent": "search",
        "enough_for_search": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "search_params": params,
        "consultation_answer": "",
        "should_offer_search": False,
    }


def _infer_missing_fields(params: dict) -> list[str]:
    """Возвращает список недостающих search-полей."""
    question = check_needs_clarification(params)
    if question == CLARIFICATION_QUESTIONS["both"]:
        return ["budget", "type"]
    if question == CLARIFICATION_QUESTIONS["budget"]:
        return ["budget"]
    if question == CLARIFICATION_QUESTIONS["type"]:
        return ["type"]
    return []


def _question_from_missing_fields(missing_fields: list, params: dict) -> str:
    """Строит уточняющий вопрос из missing_fields или fallback-логики."""
    fields = set(missing_fields or [])
    if fields == {"budget", "type"}:
        return CLARIFICATION_QUESTIONS["both"]
    if fields == {"budget"}:
        return CLARIFICATION_QUESTIONS["budget"]
    if fields == {"type"}:
        return CLARIFICATION_QUESTIONS["type"]
    return check_needs_clarification(params) or CLARIFICATION_QUESTIONS["both"]


def _merge_search_state(current_state: dict, new_params: object, intent: str) -> dict:
    """Мержит накопленное поисковое состояние с новыми параметрами, не теряя уже известное."""
    state = dict(current_state or {})
    params = new_params if isinstance(new_params, dict) else {}

    for field in ["price_min", "price_max", "type", "brand", "pickups", "sound", "style"]:
        value = params.get(field)
        if value not in (None, "", []):
            state[field] = value

    queries = params.get("search_queries")
    if isinstance(queries, list) and any(str(query or "").strip() for query in queries):
        state["search_queries"] = [str(query).strip() for query in queries if str(query or "").strip()]

    if intent in {"search", "consultation"}:
        state["last_intent"] = intent

    return state


def _finalize_search_state(state: dict) -> dict:
    """Нормализует state и вычисляет ready_for_search / missing_fields."""
    state = dict(state or {})
    params = _state_to_search_params(state)
    missing_fields = _infer_missing_fields(params)
    no_pref_fields = set(state.get("no_preference_fields") or [])
    state["missing_fields"] = [field for field in missing_fields if field not in no_pref_fields]
    state["ready_for_search"] = len(state["missing_fields"]) == 0
    state["last_clarification_target"] = (
        None if state["ready_for_search"] else _clarification_target_from_missing_fields(state["missing_fields"])
    )
    return state


def _state_to_search_params(state: dict) -> dict:
    """Преобразует session state в search params."""
    params = {
        "search_queries": state.get("search_queries") or [],
        "price_min": None if "budget" in set(state.get("no_preference_fields") or []) else state.get("price_min"),
        "price_max": None if "budget" in set(state.get("no_preference_fields") or []) else state.get("price_max"),
        "type": None if str(state.get("type") or "").strip().lower() == "any" else state.get("type"),
        "brand": state.get("brand"),
        "pickups": state.get("pickups"),
        "sound": state.get("sound"),
        "style": state.get("style"),
    }

    if not params["search_queries"] and params.get("type"):
        params["search_queries"] = [params["type"]]

    if not params["search_queries"] and str(state.get("type") or "").strip().lower() == "any":
        broad_query = _broad_query_from_state(state)
        if broad_query:
            params["search_queries"] = [broad_query]

    if not params["search_queries"]:
        broad_query = _broad_query_from_state(state)
        if broad_query:
            params["search_queries"] = [broad_query]

    return params


def _broad_query_from_state(state: dict) -> str:
    """Строит широкий запрос, если пользователь разрешил любой тип."""
    brand = str(state.get("brand") or "").strip()
    pickups = str(state.get("pickups") or "").strip()

    broad_candidates = [
        f"{brand} guitar" if brand else "",
        f"{pickups} guitar" if pickups else "",
        "guitar",
    ]

    for candidate in broad_candidates:
        if candidate:
            return candidate
    return "guitar"


def _apply_no_preference_reply(text: str, state: dict) -> dict:
    """Если пользователь ответил 'не важно/без разницы', снимает обязательность с недостающих полей."""
    if not _is_no_preference(text):
        return state

    state = dict(state or {})
    missing_fields = list(state.get("missing_fields") or [])
    clarification_target = state.get("last_clarification_target")
    if clarification_target and clarification_target not in missing_fields:
        missing_fields.append(clarification_target)
    if not missing_fields:
        return state

    no_pref_fields = set(state.get("no_preference_fields") or [])
    if clarification_target:
        no_pref_fields.add(clarification_target)
    else:
        no_pref_fields.update(missing_fields)
    state["no_preference_fields"] = sorted(no_pref_fields)

    if "type" in no_pref_fields and not str(state.get("type") or "").strip():
        state["type"] = "any"

    return state


def _clarification_target_from_missing_fields(missing_fields: list) -> Optional[str]:
    """Возвращает основной target текущего уточнения."""
    fields = list(missing_fields or [])
    if len(fields) == 1:
        return fields[0]
    return None


def _looks_like_followup_search_request(text: str) -> bool:
    """Короткие подтверждения/команды, которые при готовом state должны запускать search."""
    lower = (text or "").strip().lower()
    if not lower:
        return False

    patterns = [
        r"^(да|ага|угу|ок|окей|давай|хочу|покажи|ссылки?)$",
        r"покажи.{0,20}(вариант|ссылк|объявлен)",
        r"дай.{0,20}(ссылк|вариант)",
        r"я\s*писал\s*выше",
        r"то\s*есть\s*у\s*тебя\s*нет",
        r"тоесть\s*у\s*тебя\s*нет",
        r"у\s*тебя\s*нет.{0,40}(гитар|вариант)",
    ]
    return any(re.search(pattern, lower) for pattern in patterns)


def _should_resume_search(text: str, current_state: dict, merged_state: dict) -> bool:
    """Возвращает True, если новое сообщение должно продолжить search-контекст, а не consultation."""
    if not merged_state.get("ready_for_search"):
        return False

    if not current_state:
        return False

    if _is_no_preference(text):
        return True

    if _looks_like_followup_search_request(text):
        return True

    return False


def _build_relaxed_queries(params: dict) -> list[str]:
    """Если strict search дал 0, ослабляет запрос до более широких формулировок."""
    relaxed = []
    seen = set()

    guitar_type = str(params.get("type") or "").strip()
    brand = str(params.get("brand") or "").strip()
    queries = params.get("search_queries") or []

    def add(query: str):
        normalized = query.strip()
        if normalized and normalized.lower() not in seen:
            relaxed.append(normalized)
            seen.add(normalized.lower())

    if guitar_type:
        add(guitar_type)
        if brand:
            add(f"{brand} {guitar_type}")

    for query in queries:
        normalized = str(query or "").strip()
        if not normalized:
            continue
        words = normalized.split()
        if len(words) >= 2:
            for candidate in [words[-1], " ".join(words[-2:])]:
                if candidate.lower() != normalized.lower():
                    add(candidate)

    original = [str(query or "").strip().lower() for query in queries if str(query or "").strip()]
    return [query for query in relaxed if query.lower() not in original]
