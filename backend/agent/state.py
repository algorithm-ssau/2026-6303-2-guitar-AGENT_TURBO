"""Search state mapping and clarification state helpers.

Содержит только функции, отвечающие за состояние поиска, clarification state
и преобразование state в search params.
Оркестрация пайплайна остаётся в service.py.
"""

import os
from typing import Optional

from backend.agent.clarification import CLARIFICATION_QUESTIONS

# Константы, импортированные через service.py (не дублируем)
_ALLOWED_NO_PREFERENCE_FIELDS = {"budget", "type", "brand", "pickups", "sound", "style"}
_ALLOWED_MISSING_FIELDS_STATE = {"budget", "type"}
_SEARCH_PARAM_FIELDS = ("search_queries", "price_min", "price_max", "type", "brand", "pickups", "sound", "style")


def apply_ready_search_snapshot(route_plan: dict, current_state: Optional[dict] = None) -> dict:
    """Persists final search snapshot. Если state_action='patch' — мерджит с current_state
    (модель часто шлёт partial params в follow-up: например после "за 50" она шлёт price_max
    но забывает type=bass из state)."""
    params = route_plan["search_params"]
    current = current_state or {}
    state_action = route_plan.get("state_action", "patch")
    merge = state_action != "reset"

    def keep(field, default=None):
        new_val = params.get(field)
        if new_val is not None or not merge:
            return new_val
        return current.get(field, default)

    new_queries = list(params.get("search_queries") or [])
    queries = new_queries if (new_queries or not merge) else list(current.get("search_queries") or [])

    pending = dict(current.get("pending_defaults") or {})
    pending.pop("budget", None)
    return {
        "state_schema": "ready_search_snapshot_v1",
        "state_source": "router_search_params",
        "last_intent": "search",
        "ready_for_search": True,
        "missing_fields": [],
        "search_queries": queries,
        "price_min": keep("price_min"),
        "price_max": keep("price_max"),
        "type": keep("type"),
        "brand": keep("brand"),
        "pickups": keep("pickups"),
        "sound": keep("sound"),
        "style": keep("style"),
        "no_preference_fields": list(
            route_plan.get("no_preference_fields")
            or (current.get("no_preference_fields") if merge else [])
            or []
        ),
        "default_actions": list(route_plan.get("default_actions") or []),
        "state_action": state_action,
        "pending_defaults": pending,
        "last_clarification_target": None,
    }


def apply_incomplete_search_patch(current_state: dict, route_plan: dict) -> dict:
    """Builds clarification state by merging router output with already-known values.

    Маленькая модель router'а часто возвращает partial params в follow-up turn
    (например после "не важно" она шлёт только {"type":"any"} и забывает price_max).
    Сервер защищается: для каждого поля используем новое значение если оно явно
    задано, иначе сохраняем уже известное из current_state.

    state_action="reset" — старое игнорируем (новый поисковой контекст).
    state_action="patch" (или дефолт) — мерджим с current_state.
    """
    params = route_plan.get("search_params") if isinstance(route_plan.get("search_params"), dict) else {}
    current = current_state or {}
    state_action = route_plan.get("state_action", "patch")
    merge = state_action != "reset"

    def keep(field):
        new_val = params.get(field)
        if new_val is not None or not merge:
            return new_val
        return current.get(field)

    new_queries = list(params.get("search_queries") or [])
    queries = new_queries if (new_queries or not merge) else list(current.get("search_queries") or [])

    no_preference_fields = list(
        route_plan.get("no_preference_fields")
        or (current.get("no_preference_fields") if merge else [])
        or []
    )

    merged_price_max = keep("price_max")
    merged_price_min = keep("price_min")
    merged_type = keep("type")

    # Очищаем missing_fields от уже известных значений / явных "no_preference".
    # Маленькая модель часто включает в missing то, что уже есть в state.
    raw_missing = list(route_plan.get("missing_fields") or [])
    actually_missing = []
    for field in raw_missing:
        if field == "budget" and (merged_price_max is not None or merged_price_min is not None):
            continue
        if field == "type" and (merged_type or "type" in no_preference_fields):
            continue
        actually_missing.append(field)

    state = {
        "last_intent": "search",
        "ready_for_search": False,
        "missing_fields": actually_missing,
        "search_queries": queries,
        "price_min": merged_price_min,
        "price_max": merged_price_max,
        "type": merged_type,
        "brand": keep("brand"),
        "pickups": keep("pickups"),
        "sound": keep("sound"),
        "style": keep("style"),
        "no_preference_fields": no_preference_fields,
        "default_actions": list(route_plan.get("default_actions") or []),
        "state_action": state_action,
    }
    asked_fields = [
        field for field in (current.get("asked_fields") or [])
        if isinstance(field, str) and field in _ALLOWED_NO_PREFERENCE_FIELDS
    ]
    if asked_fields:
        state["asked_fields"] = asked_fields
    pending = dict(current.get("pending_defaults") or {})
    if route_plan.get("budget_default_offer") and state.get("price_max") is None and state.get("price_min") is None:
        pending["budget"] = {"kind": "beginner_cheap", "price_max": beginner_default_price_max()}
    if pending:
        state["pending_defaults"] = pending
    return state


def unique_preserving_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if not isinstance(value, str):
            continue
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


def beginner_default_price_max() -> float:
    raw = os.getenv("BEGINNER_DEFAULT_PRICE_MAX")
    if raw is None:
        return 500.0
    try:
        value = int(raw)
        return float(max(value, 1))
    except ValueError:
        return 500.0


def finalize_search_state(state: dict) -> dict:
    """Нормализует route-derived ready_for_search / missing_fields без semantic inference."""
    state = dict(state or {})
    missing_fields = [
        field for field in (state.get("missing_fields") or [])
        if isinstance(field, str) and field in {"budget", "type"}
    ]
    state["missing_fields"] = [] if state.get("ready_for_search") and not missing_fields else missing_fields
    state["ready_for_search"] = bool(state.get("ready_for_search")) and not state["missing_fields"]
    state["last_clarification_target"] = (
        None if state["ready_for_search"] else clarification_target_from_missing_fields(state["missing_fields"])
    )
    return state


def prepare_clarification_state(state: dict) -> dict:
    """Stores which structured fields were asked, without parsing user text."""
    state = dict(state or {})
    missing_fields = [
        field for field in (state.get("missing_fields") or [])
        if isinstance(field, str) and field in {"budget", "type"}
    ]
    asked_fields = [
        field for field in (state.get("asked_fields") or [])
        if isinstance(field, str) and field in {"budget", "type", "brand", "pickups", "sound", "style"}
    ]
    state["asked_fields"] = unique_preserving_order(asked_fields + missing_fields)
    state["missing_fields"] = missing_fields
    state["ready_for_search"] = False
    state["last_clarification_target"] = clarification_target_from_missing_fields(missing_fields)
    return state


def state_to_search_params(state: dict) -> dict:
    """Преобразует session state в execution search params."""
    if state.get("ready_for_search") and state.get("state_schema") != "ready_search_snapshot_v1":
        return empty_search_params()
    params = {
        "search_queries": state.get("search_queries") or [],
        "price_min": state.get("price_min"),
        "price_max": state.get("price_max"),
        "type": None if str(state.get("type") or "").strip().lower() == "any" else state.get("type"),
        "brand": state.get("brand"),
        "pickups": state.get("pickups"),
        "sound": state.get("sound"),
        "style": state.get("style"),
    }
    return params


def state_to_user_search_params(state: dict) -> dict:
    """Преобразует session state в user-facing searchParams."""
    params = state_to_search_params(state)
    params["type"] = state.get("type")
    return params


def search_params_to_user_search_params(params: dict) -> dict:
    return {
        "search_queries": list(params.get("search_queries") or []),
        "price_min": params.get("price_min"),
        "price_max": params.get("price_max"),
        "type": params.get("type"),
        "brand": params.get("brand"),
        "pickups": params.get("pickups"),
        "sound": params.get("sound"),
        "style": params.get("style"),
    }


def empty_search_params() -> dict:
    return {
        "search_queries": [],
        "price_min": None,
        "price_max": None,
        "type": None,
        "brand": None,
        "pickups": None,
        "sound": None,
        "style": None,
    }


def safe_router_params_for_log(params: object) -> dict:
    if not isinstance(params, dict):
        return {}
    safe = {key: params.get(key) for key in _SEARCH_PARAM_FIELDS}
    if isinstance(safe.get("search_queries"), list):
        safe["search_queries"] = [str(query)[:120] for query in safe["search_queries"][:5]]
    return safe


def clarification_target_from_missing_fields(missing_fields: list) -> Optional[str]:
    """Возвращает основной target текущего уточнения."""
    fields = list(missing_fields or [])
    if len(fields) == 1:
        return fields[0]
    return None


def question_from_missing_fields(missing_fields: list) -> str:
    """Строит уточняющий вопрос из router-provided missing_fields."""
    fields = {
        field for field in (missing_fields or [])
        if isinstance(field, str)
    }
    if fields == {"budget", "type"}:
        return CLARIFICATION_QUESTIONS["both"]
    if fields == {"budget"}:
        return CLARIFICATION_QUESTIONS["budget"]
    if fields == {"type"}:
        return CLARIFICATION_QUESTIONS["type"]
    return CLARIFICATION_QUESTIONS["both"]
