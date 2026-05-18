"""Route plan validation and normalization helpers.

Содержит только функции нормализации и валидации router-ответа.
Оркестрация пайплайна остаётся в service.py.
"""

from typing import Optional

# Константы контракта (дублированы здесь для независимости от service.py)
ALLOWED_ROUTER_INTENTS = {"search", "consultation", "off_topic", "conversation"}
ALLOWED_MISSING_FIELDS = {"budget", "type"}
ALLOWED_NO_PREFERENCE_FIELDS = {"budget", "type", "brand", "pickups", "sound", "style"}
ALLOWED_DEFAULT_ACTIONS = {"apply_beginner_budget", "accept_beginner_budget"}
ALLOWED_TYPES = {
    "stratocaster", "telecaster", "les paul", "sg", "superstrat",
    "acoustic", "classical", "bass", "seven_string", "any",
}
TYPE_ALIASES = {
    "les_paul": "les paul",
    "les paul": "les paul",
    "strat": "stratocaster",
    "tele": "telecaster",
}
PICKUPS_ALIASES = {
    "sss": "SSS",
    "ss": "SS",
    "hss": "HSS",
    "hsh": "HSH",
    "hh": "HH",
    "p90": "P90",
    "p_90": "P90",
    "p-90": "P90",
    "single coil": "single_coil",
    "single_coil": "single_coil",
    "humbuckers": "humbucker",
    "humbucker": "humbucker",
}
ALLOWED_PICKUPS = {
    "SSS", "SS", "HSS", "HSH", "HH", "P90",
    "single_coil", "humbucker", "active", "passive",
}


def candidate_intent(candidate: object) -> Optional[str]:
    """Возвращает intent из кандидата, если он допустим."""
    intent = candidate.get("intent") if isinstance(candidate, dict) else None
    if isinstance(intent, str) and intent in ALLOWED_ROUTER_INTENTS:
        return str(intent)
    return None


def normalize_route_plan(candidate: object) -> Optional[dict]:
    """Нормализует ответ router-LLM и отбрасывает невалидные структуры."""
    route_plan, _errors = validate_route_plan(candidate)
    return route_plan


def validate_route_plan(candidate: object) -> tuple[Optional[dict], list[str]]:
    """Нормализует router-ответ и возвращает конкретные ошибки контракта."""
    errors: list[str] = []
    if not isinstance(candidate, dict):
        return None, ["root must be object"]

    intent = candidate.get("intent")
    if not isinstance(intent, str) or intent not in ALLOWED_ROUTER_INTENTS:
        errors.append("intent must be one of search, consultation, off_topic, conversation")

    missing_fields = candidate.get("missing_fields")
    if not isinstance(missing_fields, list):
        errors.append("missing_fields must be list")
        normalized_missing_fields = []
    else:
        if any(not isinstance(field, str) for field in missing_fields):
            errors.append("missing_fields must contain only strings")
        normalized_missing_fields = [field for field in missing_fields if isinstance(field, str)]
        unknown_missing = [field for field in normalized_missing_fields if field not in ALLOWED_MISSING_FIELDS]
        if unknown_missing:
            errors.append("missing_fields must contain only budget/type")

    no_preference_fields = candidate.get("no_preference_fields", [])
    if no_preference_fields is None:
        no_preference_fields = []
    if not isinstance(no_preference_fields, list):
        errors.append("no_preference_fields must be list")
        normalized_no_preference_fields = []
    else:
        if any(not isinstance(field, str) for field in no_preference_fields):
            errors.append("no_preference_fields must contain only strings")
        normalized_no_preference_fields = [
            field for field in no_preference_fields
            if isinstance(field, str) and field in ALLOWED_NO_PREFERENCE_FIELDS
        ]
        if len(normalized_no_preference_fields) != len(no_preference_fields):
            errors.append("no_preference_fields must contain only allowed values")

    default_actions = candidate.get("default_actions", [])
    if default_actions is None:
        default_actions = []
    if not isinstance(default_actions, list):
        errors.append("default_actions must be list")
        normalized_default_actions = []
    else:
        if any(not isinstance(action, str) for action in default_actions):
            errors.append("default_actions must contain only strings")
        normalized_default_actions = [
            action for action in default_actions
            if isinstance(action, str) and action in ALLOWED_DEFAULT_ACTIONS
        ]
        if len(normalized_default_actions) != len(default_actions):
            errors.append("default_actions must contain only allowed values")

    state_action = candidate.get("state_action", "patch")
    if not isinstance(state_action, str) or state_action not in {"patch", "reset"}:
        errors.append("state_action must be patch or reset")
        state_action = "patch"

    budget_default_offer = bool(candidate.get("budget_default_offer"))

    enough_for_search = bool(candidate.get("enough_for_search"))
    current_turn_search = candidate.get("current_turn_search")
    if current_turn_search is not None and not isinstance(current_turn_search, bool):
        errors.append("current_turn_search must be boolean")
        current_turn_search = False

    search_params = candidate.get("search_params")
    if intent == "search":
        if not enough_for_search and normalized_missing_fields:
            normalized_search_params = (
                normalize_search_params(search_params)[0]
                if isinstance(search_params, dict)
                else None
            )
        elif not isinstance(search_params, dict):
            errors.append("search_params must be object for search intent")
            normalized_search_params = None
        else:
            normalized_search_params, param_errors = normalize_search_params(search_params)
            errors.extend(param_errors)
            if enough_for_search:
                errors.extend(validate_ready_search_params(
                    normalized_search_params,
                    normalized_missing_fields,
                    normalized_no_preference_fields,
                    normalized_default_actions,
                ))
        if not enough_for_search and not normalized_missing_fields:
            errors.append("missing_fields must contain budget and/or type when enough_for_search=false")
    elif intent == "conversation":
        if enough_for_search:
            errors.append("conversation must have enough_for_search=false")
        if normalized_missing_fields:
            errors.append("conversation must have missing_fields=[]")
        if search_params is not None:
            errors.append("search_params must be null for conversation")
        if candidate.get("should_offer_search"):
            errors.append("conversation must have should_offer_search=false")
        normalized_search_params = None
    elif search_params is not None:
        errors.append("search_params must be null for consultation/off_topic")
        normalized_search_params = None
    else:
        normalized_search_params = None

    if intent == "search" and enough_for_search and not current_turn_search:
        errors.append("ready search must include current_turn_search=true")
    if current_turn_search and not (intent == "search" and enough_for_search):
        errors.append("current_turn_search=true is allowed only for ready search")

    if errors:
        return None, errors

    return {
        "intent": intent,
        "enough_for_search": enough_for_search,
        "missing_fields": normalized_missing_fields,
        "no_preference_fields": normalized_no_preference_fields,
        "budget_default_offer": budget_default_offer,
        "default_actions": normalized_default_actions,
        "state_action": state_action,
        "search_params": normalized_search_params,
        "should_offer_search": bool(candidate.get("should_offer_search")),
        "current_turn_search": current_turn_search,
    }, []


def validate_route_plan_for_state(route_plan: dict, current_state: dict) -> list[str]:
    """Validates route contract that depends on current structured session state."""
    if route_plan.get("intent") != "search" or not route_plan.get("enough_for_search"):
        return []

    params = route_plan.get("search_params") or {}
    default_actions = {
        action for action in (route_plan.get("default_actions") or [])
        if isinstance(action, str)
    }
    has_accept_default = "accept_beginner_budget" in default_actions
    pending_budget = ((current_state or {}).get("pending_defaults") or {}).get("budget")

    errors: list[str] = []
    if has_accept_default and not pending_budget:
        errors.append("default_actions.accept_beginner_budget requires pending budget default")
    if has_accept_default and route_plan.get("state_action") == "reset":
        errors.append("default_actions.accept_beginner_budget cannot be used with state_action reset")
    if "accept_beginner_budget" in default_actions and params.get("price_max") is None:
        errors.append("accept_beginner_budget requires explicit final price_max")
    return errors


def validate_ready_search_params(
    params: Optional[dict],
    missing_fields: list[str],
    no_preference_fields: list[str],
    default_actions: list[str],
) -> list[str]:
    errors: list[str] = []
    params = params or {}
    queries = params.get("search_queries") or []
    if not queries:
        errors.append("ready search must include final search_params.search_queries")
    if not (1 <= len(queries) <= 3):
        errors.append("ready search must include 1-3 final search_params.search_queries")
    if params.get("price_max") is None and params.get("price_min") is None:
        errors.append("ready search must include explicit final search_params.price_max or price_min")
    if params.get("type") is None:
        errors.append("ready search must include explicit final search_params.type or type='any'")
    if missing_fields:
        errors.append("ready search must have missing_fields=[]")
    if params.get("price_min") is not None and params.get("price_max") is not None:
        if params["price_min"] > params["price_max"]:
            errors.append("ready search price_min must be <= price_max")
    if "apply_beginner_budget" in default_actions and params.get("price_max") is None:
        errors.append("apply_beginner_budget requires explicit final price_max")
    if "accept_beginner_budget" in default_actions and params.get("price_max") is None:
        errors.append("accept_beginner_budget requires explicit final price_max")
    if "type" in no_preference_fields and params.get("type") != "any":
        errors.append("type no_preference requires explicit final type='any'")
    if "budget" in no_preference_fields:
        errors.append("budget no_preference cannot make ready search without explicit safe budget")
    return errors


def normalize_search_params(params: dict) -> tuple[dict, list[str]]:
    """Приводит router search_params к стабильной внутренней форме."""
    errors: list[str] = []

    raw_queries = params.get("search_queries")
    queries = []
    if isinstance(raw_queries, list):
        queries = [str(query).strip() for query in raw_queries if str(query or "").strip()]

    guitar_type, type_error = normalize_type_value(params.get("type"))
    if type_error:
        errors.append(type_error)

    pickups, pickups_error = normalize_pickups_value(params.get("pickups"))
    if pickups_error:
        errors.append(pickups_error)

    normalized = {
        "search_queries": queries,
        "price_min": number_or_none(params.get("price_min")),
        "price_max": number_or_none(params.get("price_max")),
        "type": guitar_type,
        "brand": string_or_none(params.get("brand")),
        "pickups": pickups,
        "sound": string_or_none(params.get("sound")),
        "style": string_or_none(params.get("style")),
    }
    return normalized, errors


def normalize_type_value(value: object) -> tuple[Optional[str], Optional[str]]:
    if value is None:
        return None, None
    raw = str(value).strip().lower().replace("-", "_")
    if not raw:
        return None, None
    normalized = TYPE_ALIASES.get(raw, raw)
    if normalized not in ALLOWED_TYPES:
        return None, f"search_params.type must be one of {sorted(ALLOWED_TYPES)}"
    return normalized, None


def normalize_pickups_value(value: object) -> tuple[Optional[str], Optional[str]]:
    if value is None:
        return None, None
    raw = str(value).strip()
    if not raw:
        return None, None
    alias_key = raw.lower().replace("-", "_")
    normalized = PICKUPS_ALIASES.get(alias_key, PICKUPS_ALIASES.get(raw.lower(), raw))
    if normalized not in ALLOWED_PICKUPS:
        return None, f"search_params.pickups must be one of {sorted(ALLOWED_PICKUPS)}"
    return normalized, None


def number_or_none(value: object) -> Optional[float]:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def string_or_none(value: object) -> Optional[str]:
    text = str(value or "").strip()
    return text or None
