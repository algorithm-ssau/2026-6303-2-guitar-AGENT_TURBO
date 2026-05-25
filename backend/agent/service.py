"""Сервис агента: точка входа для обработки пользовательских запросов.

Связывает полный пайплайн: LLM-router → search_reverb/consultation → rank_results.
Поддерживает callback on_status для отправки промежуточных статусов.
"""

import os
import json
import time
from typing import Callable, Optional

from backend.agent.llm_client import LLMClient
from backend.agent.clarification import CLARIFICATION_QUESTIONS
from backend.agent.route_plan import (
    candidate_intent as _candidate_intent,
    validate_route_plan as _validate_route_plan,
    validate_route_plan_for_state as _validate_route_plan_for_state,
    validate_ready_search_params as _validate_ready_search_params,
    normalize_route_plan as _normalize_route_plan,
    normalize_search_params as _normalize_search_params,
    normalize_type_value as _normalize_type_value,
    normalize_pickups_value as _normalize_pickups_value,
    number_or_none as _number_or_none,
    string_or_none as _string_or_none,
    ALLOWED_ROUTER_INTENTS,
    ALLOWED_MISSING_FIELDS,
    ALLOWED_NO_PREFERENCE_FIELDS,
    ALLOWED_DEFAULT_ACTIONS,
    TYPE_ALIASES,
    ALLOWED_TYPES,
    PICKUPS_ALIASES,
    ALLOWED_PICKUPS,
)
from backend.agent.state import (
    apply_ready_search_snapshot as _apply_ready_search_snapshot,
    apply_incomplete_search_patch as _apply_incomplete_search_patch,
    unique_preserving_order as _unique_preserving_order,
    beginner_default_price_max as _beginner_default_price_max,
    finalize_search_state as _finalize_search_state,
    prepare_clarification_state as _prepare_clarification_state,
    state_to_search_params as _state_to_search_params,
    state_to_user_search_params as _state_to_user_search_params,
    search_params_to_user_search_params as _search_params_to_user_search_params,
    empty_search_params as _empty_search_params,
    safe_router_params_for_log as _safe_router_params_for_log,
    clarification_target_from_missing_fields as _clarification_target_from_missing_fields,
    question_from_missing_fields as _question_from_missing_fields,
)
from backend.agent.exceptions import (
    LLMUnavailableError,
    InvalidRouterResponseError,
    _safe_llm_unavailable_message,
)
from backend.agent.guardrails import (
    CATALOG_GUARDRAIL_ANSWER,
    MODEL_BRANDS,
    sanitize_consultation_answer as _sanitize_consultation_answer,
    sanitize_consultation_answer_result as _sanitize_consultation_answer_result,
    extract_think_block as _extract_think_block,
    compact_llm_visible_text as _compact_llm_visible_text,
    sanitize_off_topic_answer as _sanitize_off_topic_answer,
    sanitize_clarification_question as _sanitize_clarification_question,
    sanitize_conversation_answer as _sanitize_conversation_answer,
    contains_external_link_or_shop as _contains_external_link_or_shop,
    looks_like_catalog_content as _looks_like_catalog_content,
    extract_branded_model_mentions as _extract_branded_model_mentions,
    normalize_model_text as _normalize_model_text,
    is_allowed_model_mention as _is_allowed_model_mention,
    maybe_append_search_offer as _maybe_append_search_offer,
)

from backend.ranking.ranking import rank_results
from backend.search.search_reverb import search_reverb_exact
from backend.history.service import get_session_messages, get_session_state, save_session_state, strip_think_blocks
from backend.utils.logger import get_logger

logger = get_logger("agent.service")



DEFAULT_ROUTER_CONTEXT_CHAR_LIMIT = 2500
DEFAULT_ROUTER_ASSISTANT_SNIPPET_CHAR_LIMIT = 450
DEFAULT_ROUTER_MAX_PROMPT_CHARS = 4200

SEARCH_PARAM_FIELDS = ("search_queries", "price_min", "price_max", "type", "brand", "pickups", "sound", "style")
ALLOWED_ROUTER_INTENTS = {"search", "consultation", "off_topic", "conversation"}
ALLOWED_MISSING_FIELDS = {"budget", "type"}
ALLOWED_NO_PREFERENCE_FIELDS = {"budget", "type", "brand", "pickups", "sound", "style"}
ALLOWED_DEFAULT_ACTIONS = {"apply_beginner_budget", "accept_beginner_budget"}
# TYPE_ALIASES, ALLOWED_TYPES, PICKUPS_ALIASES, ALLOWED_PICKUPS imported from route_plan

_ROUTER_BAD_TIER_CACHE: dict[tuple[Optional[int], str, str], float] = {}





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


def get_off_topic_prompt() -> str:
    """Загружает промпт для безопасного off-topic отказа."""
    prompt_path = os.path.join(os.path.dirname(__file__), "../../docs/OFF_TOPIC_PROMPT.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return (
        "Ты отвечаешь на нерелевантный запрос в сервисе подбора гитар. "
        "Не отвечай на сам нерелевантный вопрос. Ответ: 1-2 предложения, по-русски, без ссылок."
    )


def get_clarification_prompt() -> str:
    """Загружает prompt для dynamic search clarification."""
    prompt_path = os.path.join(os.path.dirname(__file__), "../../docs/CLARIFICATION_PROMPT.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return (
        "Ты формулируешь короткое уточнение в сервисе подбора гитар. "
        "Задай только вопрос по missing_fields или pending default. "
        "Ответ: 1-2 предложения, по-русски, без ссылок."
    )


def get_conversation_prompt() -> str:
    """Загружает prompt для коротких non-search conversational turns."""
    prompt_path = os.path.join(os.path.dirname(__file__), "../../docs/CONVERSATION_PROMPT.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return (
        "You answer a short conversational/meta message inside a guitar search service. "
        "Do not add guitar advice or claims unless the current user message asks for them. "
        "For conversation mode, do not mention guitars, searches, results, catalogs, listings, or service context. "
        "The visible answer must use the same natural language as user_query. "
        "Answer: 1 short sentence, no links, no lists."
    )


def get_conversation_recovery_prompt() -> str:
    """Загружает stricter prompt для восстановления invalid conversational answer."""
    prompt_path = os.path.join(os.path.dirname(__file__), "../../docs/CONVERSATION_RECOVERY_PROMPT.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return (
        "Fix only the visible answer to a short conversational/meta message inside a guitar search service. "
        "Do not start search, name models, provide links, or ask for a budget. "
        "Do not add guitar advice or claims unless the current user message asks for them. "
        "For conversation mode, do not mention guitars, searches, results, catalogs, listings, or service context. "
        "The visible answer must use the same natural language as user_query. "
        "Answer: 1 short sentence, no markdown, lists, or links."
    )





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
    session_id: Optional[int] = None,
) -> dict:
    """Обрабатывает запрос пользователя через полный пайплайн.

    Пайплайн:
    - LLM-router определяет intent и search params
    - Consultation: отдельный consultation prompt отвечает текстом
    - Search: router params → search → ranking → return results/searchParams

    Args:
        text: Текстовый запрос пользователя
        llm_client: LLMClient для тестов (если None — создаётся через create_llm_client)
        search_fn: Функция поиска для тестов (если None — используется exact Reverb adapter)
        on_status: Callback для промежуточных статусов (если None — статусы не отправляются)

    Returns:
        dict с ключами mode и params/results (для поиска) или answer (для консультации)
    """
    if on_status:
        on_status("Определяю режим...")

    # Получаем LLM-клиент
    if llm_client is None:
        llm_client = create_llm_client()
    if llm_client is None:
        raise LLMUnavailableError("LLM client is not configured")

    # Выбираем функцию поиска
    actual_search_fn = search_fn or search_reverb_exact

    current_state = get_session_state(session_id) if session_id else {}
    router_history = _build_router_history(session_id)
    route_plan = _classify_query_with_retries(
        text=text,
        llm_client=llm_client,
        session_id=session_id,
        normal_history=router_history,
        current_state=current_state,
    )
    logger.info(
        "router_route intent=%s enough=%s missing=%s defaults=%s budget_offer=%s params=%s",
        route_plan["intent"],
        route_plan["enough_for_search"],
        route_plan["missing_fields"],
        route_plan.get("default_actions"),
        route_plan.get("budget_default_offer"),
        _safe_router_params_for_log(route_plan.get("search_params")),
    )

    # Серверные guards — страховка от тупняка маленькой модели router.
    route_plan = _apply_router_guards(text, route_plan, current_state, session_id)

    if route_plan["intent"] == "off_topic":
        return _handle_off_topic(text, llm_client, on_status)

    if route_plan["intent"] == "conversation":
        return _handle_conversation(
            text,
            llm_client,
            on_status,
            route_plan,
            current_state,
        )

    if route_plan["intent"] == "consultation":
        from backend.agent.context_manager import build_context
        history = build_context(session_id, get_consultation_prompt(), text, llm_client)
        return _handle_consultation(
            text,
            llm_client,
            on_status,
            history,
            should_offer_search=route_plan.get("should_offer_search", False),
            allowed_titles=_latest_search_result_titles(session_id),
            session_id=session_id,
        )

    if not route_plan.get("enough_for_search"):
        merged_state = _apply_incomplete_search_patch(current_state, route_plan)

        # Если после мерджа с current_state стало достаточно (budget + type/no_preference),
        # промоутим в поиск без повторного уточнения — модель просто забыла state.
        has_budget = merged_state.get("price_max") is not None or merged_state.get("price_min") is not None
        has_type = bool(merged_state.get("type")) or "type" in (merged_state.get("no_preference_fields") or [])
        if not merged_state.get("missing_fields") and has_budget and has_type:
            logger.info(
                "router_promoted_to_search session_id=%s price_max=%s type=%s reason=state_sufficient",
                session_id, merged_state.get("price_max"), merged_state.get("type"),
            )
            params = {
                "search_queries": list(merged_state.get("search_queries") or []),
                "price_min": merged_state.get("price_min"),
                "price_max": merged_state.get("price_max"),
                "type": merged_state.get("type"),
                "brand": merged_state.get("brand"),
                "pickups": merged_state.get("pickups"),
                "sound": merged_state.get("sound"),
                "style": merged_state.get("style"),
            }
            promoted_route_plan = dict(route_plan)
            promoted_route_plan["search_params"] = params
            promoted_route_plan["enough_for_search"] = True
            user_search_params = _search_params_to_user_search_params(params)
            promoted_state = _apply_ready_search_snapshot(promoted_route_plan, current_state)
            if session_id:
                save_session_state(session_id, promoted_state)
            from backend.agent.context_manager import build_context
            history = build_context(session_id, get_system_prompt(), text, llm_client)
            return _handle_search(
                text, llm_client, actual_search_fn, on_status, history,
                initial_params=params, display_params=user_search_params,
            )

        merged_state = _finalize_search_state(merged_state)
        merged_state = _prepare_clarification_state(merged_state)
        if session_id:
            save_session_state(session_id, merged_state)
        user_search_params = _state_to_user_search_params(merged_state)
        return _handle_clarification(text, llm_client, on_status, route_plan, merged_state, user_search_params)

    merged_state = _apply_ready_search_snapshot(route_plan, current_state)
    # Используем merged значения (с inherited от current_state) для реального execution,
    # а не raw route_plan.search_params — модель часто шлёт partial и теряет type/brand.
    params = {
        "search_queries": list(merged_state.get("search_queries") or []),
        "price_min": merged_state.get("price_min"),
        "price_max": merged_state.get("price_max"),
        "type": merged_state.get("type"),
        "brand": merged_state.get("brand"),
        "pickups": merged_state.get("pickups"),
        "sound": merged_state.get("sound"),
        "style": merged_state.get("style"),
    }
    user_search_params = _search_params_to_user_search_params(params)
    if session_id:
        save_session_state(session_id, merged_state)

    logger.info(
        "effective_search_params session_id=%s price_min=%s price_max=%s type=%s queries=%s",
        session_id,
        params.get("price_min"),
        params.get("price_max"),
        params.get("type"),
        params.get("search_queries"),
    )
    from backend.agent.context_manager import build_context
    history = build_context(session_id, get_system_prompt(), text, llm_client)
    return _handle_search(
        text,
        llm_client,
        actual_search_fn,
        on_status,
        history,
        initial_params=params,
        display_params=user_search_params,
    )


def _handle_consultation(
    text: str,
    llm_client: Optional[LLMClient],
    on_status: Optional[Callable[[str], None]],
    history: list = None,
    should_offer_search: bool = False,
    allowed_titles: Optional[list[str]] = None,
    session_id: Optional[int] = None,
) -> dict:
    """Обработка консультационного запроса."""
    if on_status:
        on_status("Формирую ответ...")

    if llm_client is None:
        raise LLMUnavailableError("LLM client is not configured")

    try:
        prompt = get_consultation_prompt()
        answer = _ask_consultation_llm(llm_client, text, prompt, history)
        if str(answer or "").startswith("Error:"):
            raise LLMUnavailableError(answer)
        answer, debug_think = _extract_think_block(answer)
        answer, block_reason = _sanitize_consultation_answer_result(answer, allowed_titles=allowed_titles)
        if block_reason:
            return _consultation_guardrail_recovery(
                block_reason,
                allowed_titles or [],
                session_id,
                text,
                llm_client,
                on_status,
            )
        answer = _maybe_append_search_offer(answer, should_offer_search)
        result = {"mode": "consultation", "answer": answer}
        if debug_think:
            result["debug_think"] = debug_think
        return result
    except LLMUnavailableError:
        raise
    except Exception as e:
        raise LLMUnavailableError(str(e)) from e


def _handle_off_topic(
    text: str,
    llm_client: Optional[LLMClient],
    on_status: Optional[Callable[[str], None]],
) -> dict:
    """Генерирует безопасный refusal для нерелевантных запросов отдельным prompt."""
    if on_status:
        on_status("Формирую ответ...")

    if llm_client is None:
        raise LLMUnavailableError("LLM client is not configured")

    prompt = get_off_topic_prompt()
    try:
        answer = _ask_consultation_llm(llm_client, text, prompt, history=None)
    except Exception as e:
        raise LLMUnavailableError(str(e)) from e
    if str(answer or "").startswith("Error:"):
        raise LLMUnavailableError(answer)
    answer, _debug_think = _extract_think_block(answer)

    try:
        answer = _sanitize_off_topic_answer(answer)
    except InvalidRouterResponseError as e:
        logger.warning("off_topic_answer_recovered reason=%s", e)
        answer = "Я помогаю с подбором гитар и музыкального оборудования. Задайте вопрос по этой теме."
    return {"mode": "consultation", "answer": answer}


def _handle_conversation(
    text: str,
    llm_client: Optional[LLMClient],
    on_status: Optional[Callable[[str], None]],
    route_plan: dict,
    current_state: dict,
) -> dict:
    """Handles non-search conversational/meta turns without touching search snapshot."""
    if on_status:
        on_status("Формирую ответ...")

    if llm_client is None:
        raise LLMUnavailableError("LLM client is not configured")

    payload = f"user_query:\n{text}"
    try:
        try:
            raw = llm_client.ask(
                payload,
                get_conversation_prompt(),
                history=None,
            )
        except TypeError:
            raw = llm_client.ask(payload, get_conversation_prompt())
    except Exception as e:
        raise LLMUnavailableError(str(e)) from e

    if str(raw or "").startswith("Error:"):
        raise LLMUnavailableError(raw)

    answer, _debug_think = _extract_think_block(raw)
    try:
        answer = _sanitize_conversation_answer(answer)
    except InvalidRouterResponseError as e:
        logger.warning("conversation_answer_invalid reason=%s", e)
        answer = _recover_conversation_answer(text, llm_client, str(e))
    return {"mode": "conversation", "answer": answer}


def _handle_clarification(
    text: str,
    llm_client: Optional[LLMClient],
    on_status: Optional[Callable[[str], None]],
    route_plan: dict,
    state: dict,
    user_search_params: Optional[dict] = None,
) -> dict:
    """Генерирует state-aware clarification без static runtime templates."""
    if on_status:
        on_status("Формирую уточнение...")

    if llm_client is None:
        raise LLMUnavailableError("LLM client is not configured")

    payload = {
        "route_plan": route_plan,
        "state": state,
        "missing_fields": state.get("missing_fields", []),
        "asked_fields": state.get("asked_fields", []),
        "no_preference_fields": state.get("no_preference_fields", []),
        "pending_defaults": state.get("pending_defaults", {}),
        "budget_default_offer": bool(route_plan.get("budget_default_offer")),
        "beginner_default_price_max": _beginner_default_price_max(),
    }
    prompt = get_clarification_prompt()
    try:
        try:
            raw = llm_client.ask(
                json.dumps(
                    {
                        "user_query": text,
                        "clarification_state": payload,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                prompt,
                history=None,
            )
        except TypeError:
            raw = llm_client.ask(json.dumps(payload, ensure_ascii=False), prompt)
    except Exception as e:
        raise LLMUnavailableError(str(e)) from e

    if str(raw or "").startswith("Error:"):
        raise LLMUnavailableError(raw)
    question, _debug_think = _extract_think_block(raw)
    try:
        question = _sanitize_clarification_question(question)
    except InvalidRouterResponseError as e:
        logger.warning("clarification_answer_recovered reason=%s", e)
        question = _question_from_missing_fields(state.get("missing_fields", []))
    return {"mode": "clarification", "question": question, "search_params": user_search_params or {}}


_MAX_CLARIFICATION_ROUNDS = 2


def _apply_router_guards(
    text: str,
    route_plan: dict,
    current_state: dict,
    session_id: Optional[int],
) -> dict:
    """Серверные guards без парсинга текста — опираются только на state.

    Guard: если router снова просит уточнение, но мы уже задали ≥N вопросов
    и в state уже есть бюджет — форсим search с тем что есть (no_preference=type
    если тип не известен). Это предохранитель от бесконечного цикла уточнений.
    """
    intent = route_plan.get("intent")
    state_budget = current_state.get("price_max") if current_state else None
    asked_fields = (current_state.get("asked_fields") if current_state else None) or []

    if (
        intent == "search"
        and not route_plan.get("enough_for_search")
        and len(asked_fields) >= _MAX_CLARIFICATION_ROUNDS
        and state_budget is not None
    ):
        logger.info(
            "router_guard_override reason=clarification_limit session_id=%s asked_fields=%s budget=%s",
            session_id, asked_fields, state_budget,
        )
        return _build_forced_search_plan(current_state)

    return route_plan


def _build_forced_search_plan(current_state: dict) -> dict:
    """Конструирует search-plan из накопленного state когда router зациклился."""
    state_type = current_state.get("type") if current_state else None
    has_type = bool(state_type)
    return {
        "intent": "search",
        "enough_for_search": True,
        "current_turn_search": True,
        "missing_fields": [],
        "no_preference_fields": [] if has_type else ["type"],
        "state_action": "patch",
        "search_params": {
            "search_queries": list((current_state.get("search_queries") if current_state else None) or []),
            "price_min": current_state.get("price_min") if current_state else None,
            "price_max": current_state.get("price_max") if current_state else None,
            "type": state_type if has_type else "any",
            "brand": current_state.get("brand") if current_state else None,
            "pickups": current_state.get("pickups") if current_state else None,
            "sound": current_state.get("sound") if current_state else None,
            "style": current_state.get("style") if current_state else None,
        },
        "should_offer_search": False,
    }


def _handle_search(
    text: str,
    llm_client: Optional[LLMClient],
    search_fn,
    on_status: Optional[Callable[[str], None]],
    history: Optional[list] = None,
    initial_params: Optional[dict] = None,
    display_params: Optional[dict] = None,
) -> dict:
    """Обработка поискового запроса."""
    # Генерация параметров поиска
    if on_status:
        on_status("Генерирую параметры поиска...")

    if initial_params is None:
        raise InvalidRouterResponseError("Search path requires router-provided search_params")
    params = initial_params

    # Поиск на Reverb
    if on_status:
        on_status("Ищу на Reverb...")

    try:
        results = search_fn(
            params.get("search_queries", []),
            params.get("price_min"),
            params.get("price_max"),
            type=params.get("type"),
        )
    except Exception as e:
        logger.error("Ошибка search_reverb: %s", e)
        return {
            "mode": "search",
            "results": [],
            "error": "Не удалось выполнить поиск. Попробуйте позже.",
            "search_params": display_params,
        }

    # Ранжирование результатов
    if on_status:
        on_status("Ранжирую результаты...")

    try:
        rank_params = {
            "budget_max": params.get("price_max"),
            "search_queries": params.get("search_queries", []),
            "type": None if str(params.get("type") or "").strip().lower() == "any" else params.get("type"),
            "pickups": params.get("pickups"),
            "brand": params.get("brand"),
            "sound": params.get("sound"),
            "style": params.get("style"),
        }
        ranked = rank_results(results, rank_params)
    except Exception as e:
        logger.error("Ошибка rank_results, возвращаю неранжированные: %s", e)
        ranked = results[:5]

    response = {"mode": "search", "results": ranked, "search_params": display_params}
    if not ranked:
        explanation, actions = _build_empty_search_fallback(params, search_fn)
        response["fallback_explanation"] = explanation
        if actions:
            response["actions"] = actions
    return response


def _build_empty_search_fallback(params: dict, search_fn) -> tuple[str, list[dict]]:
    """При 0 результатов формирует утвердительное объяснение (без вопросов!)
    и список actionable suggestions для UI-кнопок."""
    queries = params.get("search_queries") or []
    price_max = params.get("price_max")
    type_value = params.get("type")
    pretty_query = ", ".join(queries) if queries else "вашему запросу"

    def safe_search(q, pmin, pmax, t):
        try:
            return search_fn(q, pmin, pmax, type=t) or []
        except Exception:
            return []

    # 1. Был query+budget — самый дешёвый matching query без budget
    if price_max is not None and queries:
        without_budget = safe_search(queries, None, None, type_value)
        if without_budget:
            cheapest = min(without_budget, key=lambda x: x.get("price") or float("inf"))
            cheapest_price = cheapest.get("price")
            if cheapest_price and cheapest_price > price_max:
                bumped = _round_budget_up(cheapest_price)
                text = (
                    f"По запросу «{pretty_query}» под ${int(price_max)} ничего нет. "
                    f"Минимум — ${int(cheapest_price)} ({cheapest.get('title','')[:80]})."
                )
                actions = [{
                    "kind": "search_with_budget",
                    "label": f"Показать варианты до ${bumped}",
                    "price_max": bumped,
                    "type": type_value,
                    "search_queries": queries,
                }]
                return text, actions

    # 2. Был budget — что-нибудь в budget без query, с типом
    if price_max is not None:
        in_budget_typed = safe_search([], None, price_max, type_value)
        if in_budget_typed:
            cheapest = min(in_budget_typed, key=lambda x: x.get("price") or float("inf"))
            text = (
                f"В бюджете до ${int(price_max)} есть {len(in_budget_typed)} вариантов без фильтра по модели "
                f"(например {cheapest.get('title','')[:60]} за ${int(cheapest.get('price') or 0)})."
            )
            actions = [{
                "kind": "search_with_budget",
                "label": "Показать всё в моём бюджете",
                "price_max": price_max,
                "type": type_value,
                "search_queries": [],
            }]
            return text, actions

    # 3. Cheapest в типе вообще без budget
    if price_max is not None and type_value and str(type_value).strip().lower() != "any":
        in_type = safe_search([], None, None, type_value)
        if in_type:
            cheapest = min(in_type, key=lambda x: x.get("price") or float("inf"))
            cheapest_price = int(cheapest.get("price") or 0)
            bumped = _round_budget_up(cheapest_price)
            text = (
                f"В типе «{type_value}» под ${int(price_max)} ничего нет. "
                f"Минимум — ${cheapest_price} ({cheapest.get('title','')[:70]})."
            )
            actions = [{
                "kind": "search_with_budget",
                "label": f"Показать варианты до ${bumped}",
                "price_max": bumped,
                "type": type_value,
                "search_queries": [],
            }]
            return text, actions

    # 4. Cheapest в базе вообще
    if price_max is not None:
        all_items = safe_search([], None, None, None)
        if all_items:
            cheapest = min(all_items, key=lambda x: x.get("price") or float("inf"))
            cheapest_price = int(cheapest.get("price") or 0)
            bumped = _round_budget_up(cheapest_price)
            text = (
                f"Под ${int(price_max)} в базе ничего нет. "
                f"Самая дешёвая гитара — ${cheapest_price} ({cheapest.get('title','')[:70]})."
            )
            actions = [{
                "kind": "search_with_budget",
                "label": f"Показать варианты до ${bumped}",
                "price_max": bumped,
                "type": None,
                "search_queries": [],
            }]
            return text, actions

    return ("По заданным параметрам ничего не найдено.", [])


def _round_budget_up(price: float) -> int:
    """Округляет до приятной круглой суммы выше цены (159 → 200, 1680 → 1700)."""
    p = int(price)
    if p < 100:
        return ((p // 10) + 1) * 10
    if p < 1000:
        return ((p // 50) + 1) * 50
    return ((p // 100) + 1) * 100


DEFAULT_ANSWER_MAX_HISTORY_CHARS = 10000


def _answer_max_history_chars() -> int:
    return _env_int("ANSWER_MAX_HISTORY_CHARS", DEFAULT_ANSWER_MAX_HISTORY_CHARS, minimum=1000)


def _truncate_history_by_chars(history: Optional[list], max_chars: int) -> Optional[list]:
    """Оставляет только последние сообщения, суммарно вмещающиеся в max_chars.

    Нужно, чтобы answer-модель (consultation/off_topic) не упиралась в
    per-request лимит провайдера на длинной истории диалога — аналог emergency-tier
    у router'а, но для answer-вызова."""
    if not history:
        return history
    kept: list = []
    total = 0
    for msg in reversed(history):
        content = str(msg.get("content") or "")
        size = len(content)
        if kept and total + size > max_chars:
            break
        kept.append(msg)
        total += size
    kept.reverse()
    if len(kept) < len(history):
        logger.info(
            "answer_history_truncated kept=%d/%d chars=%d max=%d",
            len(kept), len(history), total, max_chars,
        )
    return kept


def _ask_consultation_llm(
    llm_client: LLMClient,
    text: str,
    prompt: str,
    history: Optional[list],
) -> str:
    """Вызывает LLM с history, но совместим со старыми сигнатурами ask()."""
    history = _truncate_history_by_chars(history, _answer_max_history_chars())
    try:
        return llm_client.ask(text, prompt, history=history)
    except TypeError:
        return llm_client.ask(text, prompt)





def _consultation_guardrail_recovery(
    reason: str,
    allowed_titles: list[str],
    session_id: Optional[int],
    text: str = "",
    llm_client: Optional[LLMClient] = None,
    on_status: Optional[Callable[[str], None]] = None,
) -> dict:
    """Преобразует sanitizer block во внешний UX без утечки backend fallback."""
    if allowed_titles:
        last_index = min(len(allowed_titles), 5)
        return {
            "mode": "consultation",
            "answer": (
                f"Могу сравнивать только варианты из последней выдачи (#1-#{last_index}). "
                "Если хотите новые варианты, напишите бюджет и тип инструмента."
            ),
        }

    recovery_state = _prepare_clarification_state({
        "last_intent": "search",
        "missing_fields": ["budget", "type"],
        "ready_for_search": False,
    })
    if session_id:
        save_session_state(session_id, recovery_state)
    route_plan = {
        "intent": "search",
        "enough_for_search": False,
        "missing_fields": ["budget", "type"],
        "no_preference_fields": [],
        "budget_default_offer": False,
        "default_actions": [],
        "state_action": "patch",
        "search_params": None,
        "should_offer_search": False,
        "guardrail_reason": reason,
    }
    return _handle_clarification(
        text,
        llm_client,
        on_status,
        route_plan,
        recovery_state,
        _state_to_user_search_params(recovery_state),
    )





def _env_int(name: str, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(value, minimum)


def _router_message_size(messages: list[dict]) -> int:
    return sum(len(str(message.get("content") or "")) for message in messages)


def _router_bad_tier_ttl_seconds() -> int:
    return _env_int("ROUTER_BAD_TIER_TTL_SECONDS", 600, minimum=30)


def _router_tier_cache_key(session_id: Optional[int], model: str, tier: str) -> tuple[Optional[int], str, str]:
    return (session_id, model, tier)


def _is_router_tier_known_bad(session_id: Optional[int], model: str, tier: str) -> bool:
    if session_id is None:
        return False
    key = _router_tier_cache_key(session_id, model, tier)
    expires_at = _ROUTER_BAD_TIER_CACHE.get(key)
    if not expires_at:
        return False
    if expires_at <= time.monotonic():
        _ROUTER_BAD_TIER_CACHE.pop(key, None)
        return False
    return True


def _mark_router_tier_known_bad(session_id: Optional[int], model: str, tier: str) -> None:
    if session_id is None:
        return
    _ROUTER_BAD_TIER_CACHE[_router_tier_cache_key(session_id, model, tier)] = (
        time.monotonic() + _router_bad_tier_ttl_seconds()
    )


def _is_request_too_large_error(error: object) -> bool:
    lowered = str(error or "").lower()
    return (
        "request_too_large" in lowered
        or "request entity too large" in lowered
        or "error code: 413" in lowered
        or "status code: 413" in lowered
    )


def _router_context_stats(text: str, history: list, current_state: dict) -> dict:
    from backend.agent.llm_client import build_router_prompt_for_debug, get_router_llm_model

    prompt = build_router_prompt_for_debug(text, history=history, current_state=current_state)
    return {
        "model": get_router_llm_model(),
        "history_messages": len(history or []),
        "history_chars": sum(len(str(item.get("content") or "")) for item in (history or [])),
        "prompt_chars": len(prompt),
    }


def _router_repair_context_stats(
    text: str,
    candidate: object,
    errors: list[str],
    history: list,
    current_state: dict,
) -> dict:
    from backend.agent.llm_client import build_router_repair_prompt_for_debug, get_router_llm_model

    prompt = build_router_repair_prompt_for_debug(
        text,
        invalid_plan=candidate if isinstance(candidate, dict) else {"raw": candidate},
        validation_errors=errors,
        history=history,
        current_state=current_state,
    )
    return {
        "model": get_router_llm_model(),
        "history_messages": len(history or []),
        "history_chars": sum(len(str(item.get("content") or "")) for item in (history or [])),
        "prompt_chars": len(prompt),
    }


def _router_recovery_context_stats(
    text: str,
    candidate: object,
    errors: list[str],
    history: list,
    current_state: dict,
) -> dict:
    from backend.agent.llm_client import build_router_recovery_prompt_for_debug, get_router_llm_model

    prompt = build_router_recovery_prompt_for_debug(
        text,
        invalid_plan=candidate if isinstance(candidate, dict) else {"raw": candidate},
        validation_errors=errors,
        history=history,
        current_state=current_state,
    )
    return {
        "model": get_router_llm_model(),
        "history_messages": len(history or []),
        "history_chars": sum(len(str(item.get("content") or "")) for item in (history or [])),
        "prompt_chars": len(prompt),
    }


def _router_max_prompt_chars() -> int:
    # Safety budget for router cost/latency; this is not the provider context window.
    return _env_int("ROUTER_MAX_PROMPT_CHARS", DEFAULT_ROUTER_MAX_PROMPT_CHARS, minimum=1200)


def _router_prompt_too_large(stats: dict) -> bool:
    return int(stats.get("prompt_chars") or 0) > _router_max_prompt_chars()


def _log_router_context_stats(tier: str, stats: dict) -> None:
    logger.info(
        "LLM-router context tier=%s model=%s history_messages=%s history_chars=%s prompt_chars=%s",
        tier,
        stats["model"],
        stats["history_messages"],
        stats["history_chars"],
        stats["prompt_chars"],
    )


def _log_router_repair_context_stats(tier: str, stats: dict) -> None:
    logger.info(
        "LLM-router repair context tier=%s model=%s history_messages=%s history_chars=%s prompt_chars=%s",
        tier,
        stats["model"],
        stats["history_messages"],
        stats["history_chars"],
        stats["prompt_chars"],
    )


def _log_router_recovery_context_stats(tier: str, stats: dict) -> None:
    logger.info(
        "LLM-router recovery context tier=%s model=%s history_messages=%s history_chars=%s prompt_chars=%s",
        tier,
        stats["model"],
        stats["history_messages"],
        stats["history_chars"],
        stats["prompt_chars"],
    )





def _recover_conversation_answer(
    text: str,
    llm_client: LLMClient,
    validation_error: str,
) -> str:
    payload = {
        "user_query": text,
        "validation_error": validation_error,
    }
    prompt = get_conversation_recovery_prompt()
    try:
        try:
            raw = llm_client.ask(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                prompt,
                history=None,
            )
        except TypeError:
            raw = llm_client.ask(json.dumps(payload, ensure_ascii=False), prompt)
    except Exception as e:
        raise LLMUnavailableError(str(e)) from e

    if str(raw or "").startswith("Error:"):
        raise LLMUnavailableError(raw)

    answer, _debug_think = _extract_think_block(raw)
    try:
        return _sanitize_conversation_answer(answer)
    except InvalidRouterResponseError as e:
        logger.warning("conversation_answer_recovery_failed reason=%s", e)
        raise LLMUnavailableError("Conversation answer recovery failed") from e





def _latest_search_result_titles(session_id: Optional[int]) -> list[str]:
    """Возвращает title из последней search-выдачи без разбора user text."""
    if not session_id:
        return []
    try:
        items = get_session_messages(session_id)
    except Exception as e:
        logger.error("Ошибка чтения search titles для sanitizer: %s", e)
        return []
    for item in reversed(items):
        if item.get("mode") != "search":
            continue
        titles: list[str] = []
        for result in item.get("results") or []:
            title = str(result.get("title") or "").strip()
            if title:
                titles.append(title)
        return titles[:5]
    return []





def _build_router_history(session_id: Optional[int]) -> list:
    """Готовит компактную историю диалога для LLM-router."""
    if not session_id:
        return []

    try:
        items = get_session_messages(session_id)
    except Exception as e:
        logger.error("Ошибка чтения истории для router: %s", e)
        return []

    latest_search_index = None
    for index, item in enumerate(items):
        if item.get("mode") == "search" and item.get("results"):
            latest_search_index = index

    selected_items = list(enumerate(items))[-8:]
    selected_indices = {index for index, _ in selected_items}
    if latest_search_index is not None and latest_search_index not in selected_indices:
        selected_items = [(latest_search_index, items[latest_search_index])] + selected_items[-7:]
    selected_items = sorted({index: item for index, item in selected_items}.items())

    snippet_limit = _env_int(
        "ROUTER_ASSISTANT_SNIPPET_CHAR_LIMIT",
        DEFAULT_ROUTER_ASSISTANT_SNIPPET_CHAR_LIMIT,
        minimum=120,
    )
    blocks: list[dict] = []
    for absolute_index, item in selected_items:
        user_content = _compact_llm_visible_text(item.get("user_query", ""), limit=350)
        if item.get("mode") == "search" and item.get("results"):
            from backend.agent.context_manager import format_search_results_context
            assistant = format_search_results_context(
                item.get("results", []),
                latest=absolute_index == latest_search_index,
            )
        else:
            assistant = _compact_llm_visible_text(item.get("answer") or "", limit=snippet_limit)
        messages = []
        if user_content:
            messages.append({"role": "user", "content": user_content})
        if assistant:
            messages.append({"role": "assistant", "content": assistant})
        if messages:
            blocks.append({
                "messages": messages,
                "is_latest_search": absolute_index == latest_search_index,
            })

    char_limit = _env_int(
        "ROUTER_CONTEXT_CHAR_LIMIT",
        DEFAULT_ROUTER_CONTEXT_CHAR_LIMIT,
        minimum=800,
    )
    while blocks and sum(_router_message_size(block["messages"]) for block in blocks) > char_limit:
        removable_index = next(
            (index for index, block in enumerate(blocks) if not block["is_latest_search"]),
            None,
        )
        if removable_index is None:
            break
        blocks.pop(removable_index)

    history = []
    for block in blocks:
        history.extend(block["messages"])
    return history


def _build_emergency_router_history(session_id: Optional[int]) -> list:
    """Готовит минимальный context для retry после provider 413."""
    if not session_id:
        return []

    try:
        items = get_session_messages(session_id)
    except Exception as e:
        logger.error("Ошибка чтения emergency history для router: %s", e)
        return []

    latest_search_index = None
    for index, item in enumerate(items):
        if item.get("mode") == "search" and item.get("results"):
            latest_search_index = index

    history = []
    if latest_search_index is not None:
        from backend.agent.context_manager import format_search_results_context
        history.append({
            "role": "assistant",
            "content": format_search_results_context(
                items[latest_search_index].get("results", []),
                latest=True,
            ),
        })

    recent_users = []
    for item in reversed(items):
        query = _compact_llm_visible_text(item.get("user_query", ""), limit=220)
        if query:
            recent_users.append(query)
        if len(recent_users) >= 2:
            break

    for query in reversed(recent_users):
        history.append({"role": "user", "content": query})

    return history


def _classify_query_with_retries(
    text: str,
    llm_client: LLMClient,
    session_id: Optional[int],
    normal_history: list,
    current_state: dict,
) -> dict:
    """Классифицирует запрос, автоматически ужимая context после provider 413."""
    attempts = [
        ("normal", normal_history),
        ("emergency", _build_emergency_router_history(session_id)),
        ("stateless", []),
    ]
    last_error: Optional[LLMUnavailableError] = None
    from backend.agent.llm_client import get_router_llm_model
    router_model = get_router_llm_model()

    for tier, history in attempts:
        if _is_router_tier_known_bad(session_id, router_model, tier):
            logger.info(
                "LLM-router context tier=%s skipped locally: known bad for model=%s",
                tier,
                router_model,
            )
            continue
        try:
            stats = _router_context_stats(text, history, current_state)
        except Exception as e:
            logger.warning("Не удалось посчитать router context stats tier=%s: %s", tier, e)
            stats = {
                "model": router_model,
                "history_messages": len(history or []),
                "history_chars": sum(len(str(item.get("content") or "")) for item in (history or [])),
                "prompt_chars": 0,
            }
        _log_router_context_stats(tier, stats)
        if _router_prompt_too_large(stats):
            logger.warning(
                "LLM-router context tier=%s skipped locally: prompt_chars=%s exceeds max=%s",
                tier,
                stats["prompt_chars"],
                _router_max_prompt_chars(),
            )
            continue
        try:
            return _classify_query(
                text,
                llm_client,
                history,
                current_state,
                repair_histories=_router_repair_history_attempts(session_id, tier, history),
            )
        except LLMUnavailableError as e:
            last_error = e
            provider_error = e.__cause__ or e
            if not _is_request_too_large_error(provider_error):
                raise
            _mark_router_tier_known_bad(session_id, router_model, tier)
            if tier == "stateless":
                break
            logger.warning(
                "LLM-router request too large on tier=%s; retrying with more compact context",
                tier,
            )

    raise LLMUnavailableError(
        "LLM-router request failed after context compaction",
        user_message=_safe_llm_unavailable_message(
            (last_error.__cause__ if last_error and last_error.__cause__ else last_error)
            or "request_too_large"
        ),
    )


def _classify_query(
    text: str,
    llm_client: LLMClient,
    history: list,
    current_state: dict,
    repair_histories: Optional[list[tuple[str, list]]] = None,
) -> dict:
    """Определяет сценарий через обязательный LLM-router."""
    try:
        candidate = llm_client.classify_and_plan_query(text, history=history, current_state=current_state)
    except Exception as e:
        logger.error("LLM-router unavailable: %s", e)
        raise LLMUnavailableError("LLM-router request failed", user_message=_safe_llm_unavailable_message(e)) from e

    route_plan, errors = _validate_route_plan(candidate)
    if route_plan is not None:
        state_errors = _validate_route_plan_for_state(route_plan, current_state)
        if state_errors:
            route_plan = None
            errors = state_errors
    if route_plan is None:
        logger.warning(
            "Invalid LLM-router response; evaluating repair: errors=%s candidate=%r",
            errors,
            candidate,
        )
        original_intent = _candidate_intent(candidate)

        repair_errors = errors
        repaired = None
        if _is_repairable_router_error(errors):
            for repaired in _iter_repaired_route_plans(
                llm_client,
                text,
                candidate,
                errors,
                repair_histories or [("current", history or [])],
                current_state,
            ):
                route_plan, repair_errors = _validate_route_plan(repaired)
                if route_plan is not None:
                    state_repair_errors = _validate_route_plan_for_state(route_plan, current_state)
                    if state_repair_errors:
                        route_plan = None
                        repair_errors = state_repair_errors
                if route_plan is None:
                    logger.warning(
                        "Invalid LLM-router repair candidate: errors=%s repaired=%r",
                        repair_errors,
                        repaired,
                    )
                    continue
                if original_intent is not None and route_plan["intent"] != original_intent:
                    logger.warning(
                        "router_repair_candidate_rejected reason=intent_changed original_intent=%s repaired_intent=%s",
                        original_intent,
                        route_plan["intent"],
                    )
                    route_plan = None
                    repair_errors = ["router repair changed valid original intent"]
                    continue

                logger.info("router_repair_succeeded intent=%s", route_plan["intent"])
                break
        else:
            logger.info("router_repair_skipped reason=non_repairable errors=%s", errors)

        if route_plan is None:
            recovery_errors = repair_errors
            recovered = None
            for recovered in _iter_recovered_route_plans(
                llm_client,
                text,
                repaired if isinstance(repaired, dict) else candidate,
                repair_errors,
                repair_histories or [("current", history or [])],
                current_state,
            ):
                route_plan, recovery_errors = _validate_route_plan(recovered)
                if route_plan is not None:
                    state_recovery_errors = _validate_route_plan_for_state(route_plan, current_state)
                    if state_recovery_errors:
                        route_plan = None
                        recovery_errors = state_recovery_errors
                if route_plan is not None and route_plan.get("enough_for_search"):
                    route_plan = None
                    recovery_errors = ["router recovery must not return ready search"]
                if route_plan is None:
                    logger.warning(
                        "Invalid LLM-router recovery candidate: errors=%s recovered=%r",
                        recovery_errors,
                        recovered,
                    )
                    continue
                break
            if route_plan is None:
                logger.error(
                    "Invalid LLM-router response after recovery: errors=%s candidate=%r repaired=%r recovered=%r",
                    recovery_errors,
                    candidate,
                    repaired,
                    recovered,
                )
                route_plan = _fallback_incomplete_route_from_state(current_state)
                logger.warning("router_recovery_fell_back_to_state missing=%s", route_plan["missing_fields"])

            logger.info("router_recovery_succeeded intent=%s", route_plan["intent"])

    return route_plan


def _router_repair_history_attempts(
    session_id: Optional[int],
    current_tier: str,
    current_history: list,
) -> list[tuple[str, list]]:
    if current_tier == "stateless":
        return [("stateless", [])]
    if current_tier == "emergency":
        return [("emergency", current_history or []), ("stateless", [])]
    return [
        ("emergency", _build_emergency_router_history(session_id)),
        ("stateless", []),
    ]


def _iter_repaired_route_plans(
    llm_client: LLMClient,
    text: str,
    candidate: object,
    errors: list[str],
    repair_histories: list[tuple[str, list]],
    current_state: dict,
):
    repair_method = getattr(llm_client, "repair_router_plan", None)
    if not callable(repair_method):
        logger.info("router_repair_skipped reason=no_repair_method errors=%s", errors)
        return

    attempted = False
    skipped_for_size = False
    for tier, history in repair_histories:
        stats = _router_repair_context_stats(text, candidate, errors, history or [], current_state)
        _log_router_repair_context_stats(tier, stats)
        if _router_prompt_too_large(stats):
            skipped_for_size = True
            logger.warning(
                "router_repair_skipped reason=prompt_too_large tier=%s prompt_chars=%s max=%s",
                tier,
                stats["prompt_chars"],
                _router_max_prompt_chars(),
            )
            continue
        try:
            attempted = True
            logger.info("router_repair_attempted tier=%s errors=%s", tier, errors)
            yield repair_method(
                text,
                candidate if isinstance(candidate, dict) else {"raw": candidate},
                errors,
                history=history,
                current_state=current_state,
            )
        except Exception as e:
            logger.error("LLM-router repair unavailable: %s", e)
            raise LLMUnavailableError("LLM-router repair request failed", user_message=_safe_llm_unavailable_message(e)) from e

    if skipped_for_size and not attempted:
        logger.info("router_repair_skipped reason=all_prompts_too_large errors=%s", errors)


def _iter_recovered_route_plans(
    llm_client: LLMClient,
    text: str,
    invalid_plan: object,
    errors: list[str],
    repair_histories: list[tuple[str, list]],
    current_state: dict,
) -> object:
    recovery_method = getattr(llm_client, "recover_router_plan", None)
    if not callable(recovery_method):
        logger.info("router_recovery_skipped reason=no_recovery_method errors=%s", errors)
        return

    attempted = False
    skipped_for_size = False
    for tier, history in repair_histories:
        stats = _router_recovery_context_stats(text, invalid_plan, errors, history or [], current_state)
        _log_router_recovery_context_stats(tier, stats)
        if _router_prompt_too_large(stats):
            skipped_for_size = True
            logger.warning(
                "router_recovery_skipped reason=prompt_too_large tier=%s prompt_chars=%s max=%s",
                tier,
                stats["prompt_chars"],
                _router_max_prompt_chars(),
            )
            continue
        try:
            attempted = True
            logger.info("router_recovery_attempted tier=%s errors=%s", tier, errors)
            yield recovery_method(
                text,
                invalid_plan if isinstance(invalid_plan, dict) else {"raw": invalid_plan},
                errors,
                history=history,
                current_state=current_state,
            )
        except Exception as e:
            logger.error("LLM-router recovery unavailable: %s", e)
            raise LLMUnavailableError("LLM-router recovery request failed", user_message=_safe_llm_unavailable_message(e)) from e

    if skipped_for_size and not attempted:
        logger.info("router_recovery_skipped reason=all_prompts_too_large errors=%s", errors)


def _fallback_incomplete_route_from_state(current_state: dict) -> dict:
    """Last-resort contract fallback: no semantic inference, no executable search."""
    state = current_state or {}
    missing_fields = [
        field for field in (state.get("missing_fields") or ["budget", "type"])
        if isinstance(field, str) and field in ALLOWED_MISSING_FIELDS
    ]
    if not missing_fields:
        missing_fields = ["budget", "type"]
    params = {
        "search_queries": list(state.get("search_queries") or []),
        "price_min": state.get("price_min"),
        "price_max": state.get("price_max"),
        "type": state.get("type"),
        "brand": state.get("brand"),
        "pickups": state.get("pickups"),
        "sound": state.get("sound"),
        "style": state.get("style"),
    }
    return {
        "intent": "search",
        "enough_for_search": False,
        "missing_fields": missing_fields,
        "no_preference_fields": [
            field for field in (state.get("no_preference_fields") or [])
            if isinstance(field, str) and field in ALLOWED_NO_PREFERENCE_FIELDS
        ],
        "budget_default_offer": False,
        "default_actions": [],
        "state_action": "patch",
        "search_params": params,
        "should_offer_search": False,
        "current_turn_search": False,
    }


def _is_repairable_router_error(errors: list[str]) -> bool:
    if not errors:
        return False
    non_repairable = {
        "root must be object",
        "intent must be one of search, consultation, off_topic, conversation",
    }
    return all(error not in non_repairable for error in errors)


# _candidate_intent, _normalize_route_plan, _validate_route_plan imported from route_plan





# _question_from_missing_fields, _apply_ready_search_snapshot, _apply_incomplete_search_patch,
# _unique_preserving_order, _beginner_default_price_max, _finalize_search_state,
# _prepare_clarification_state, _state_to_search_params, _state_to_user_search_params,
# _search_params_to_user_search_params, _empty_search_params, _safe_router_params_for_log,
# _clarification_target_from_missing_fields — all imported from backend.agent.state
