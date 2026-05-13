"""КЛИЕНТ GROQ LLM"""
import json
import os
from typing import Optional

from groq import Groq

DEFAULT_ROUTER_MODEL = "llama-3.1-8b-instant"
DEFAULT_ANSWER_MODEL = "llama-3.3-70b-versatile"


class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        self.client = Groq(api_key=self.api_key)
        self.base_model = os.getenv("LLM_MODEL")
        # Router intentionally does not inherit LLM_MODEL: answer models like groq/compound are too heavy for JSON routing.
        self.router_model = os.getenv("LLM_ROUTER_MODEL", DEFAULT_ROUTER_MODEL)
        self.answer_model = os.getenv("LLM_ANSWER_MODEL", self.base_model or DEFAULT_ANSWER_MODEL)
        self.model = self.answer_model

    def ask(self, user_message: str, system_prompt: str, history: list = None) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        # Добавляем историю диалога (если есть)
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        try:
            response = self.client.chat.completions.create(
                model=self.answer_model,
                messages=messages,
                temperature=0.0
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def summarize(self, messages: list, prompt: str) -> str:
        """Делает суммаризацию переданных сообщений."""
        transcript = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        try:
            response = self.client.chat.completions.create(
                model=self.answer_model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": transcript}
                ],
                temperature=0.0
            )
            return response.choices[0].message.content
        except Exception:
            return ""

    def classify_and_plan_query(
        self,
        user_message: str,
        history: Optional[list] = None,
        current_state: Optional[dict] = None,
    ) -> dict:
        prompt = _build_router_prompt(
            user_message,
            _format_history_for_search(history),
            current_state or {},
        )

        response = self.client.chat.completions.create(
            model=self.router_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if not isinstance(content, str):
            return {}
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def repair_router_plan(
        self,
        user_message: str,
        invalid_plan: dict,
        validation_errors: list[str],
        history: Optional[list] = None,
        current_state: Optional[dict] = None,
    ) -> dict:
        prompt = _build_router_repair_prompt(
            user_message,
            _format_history_for_search(history),
            current_state or {},
            invalid_plan,
            validation_errors,
        )

        response = self.client.chat.completions.create(
            model=self.router_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if not isinstance(content, str):
            return {}
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def recover_router_plan(
        self,
        user_message: str,
        invalid_plan: dict,
        validation_errors: list[str],
        history: Optional[list] = None,
        current_state: Optional[dict] = None,
    ) -> dict:
        prompt = _build_router_recovery_prompt(
            user_message,
            _format_history_for_search(history),
            current_state or {},
            invalid_plan,
            validation_errors,
        )

        response = self.client.chat.completions.create(
            model=self.router_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if not isinstance(content, str):
            return {}
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def clarify_search(self, user_message: str, system_prompt: str, payload: dict) -> str:
        """Generates a short search clarification from structured backend state."""
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "user_query": user_message,
                        "clarification_state": payload or {},
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            },
        ]
        try:
            response = self.client.chat.completions.create(
                model=self.answer_model,
                messages=messages,
                temperature=0.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"


def get_llm_client():
    """Compatibility wrapper for service.py"""
    return LLMClient().client

def get_llm_model():
    return os.getenv("LLM_MODEL", DEFAULT_ANSWER_MODEL)


def get_router_llm_model():
    return os.getenv("LLM_ROUTER_MODEL", DEFAULT_ROUTER_MODEL)


def get_answer_llm_model():
    return os.getenv("LLM_ANSWER_MODEL", os.getenv("LLM_MODEL", DEFAULT_ANSWER_MODEL))


def build_router_prompt_for_debug(
    user_message: str,
    history: Optional[list] = None,
    current_state: Optional[dict] = None,
) -> str:
    """Builds the exact router prompt for diagnostics without calling LLM."""
    return _build_router_prompt(
        user_message,
        _format_history_for_search(history),
        current_state or {},
    )


def build_router_repair_prompt_for_debug(
    user_message: str,
    invalid_plan: dict,
    validation_errors: list[str],
    history: Optional[list] = None,
    current_state: Optional[dict] = None,
) -> str:
    """Builds the exact router repair prompt for diagnostics without calling LLM."""
    return _build_router_repair_prompt(
        user_message,
        _format_history_for_search(history),
        current_state or {},
        invalid_plan,
        validation_errors,
    )


def build_router_recovery_prompt_for_debug(
    user_message: str,
    invalid_plan: dict,
    validation_errors: list[str],
    history: Optional[list] = None,
    current_state: Optional[dict] = None,
) -> str:
    """Builds the exact router recovery prompt for diagnostics without calling LLM."""
    return _build_router_recovery_prompt(
        user_message,
        _format_history_for_search(history),
        current_state or {},
        invalid_plan,
        validation_errors,
    )


def _format_history_for_search(history: Optional[list]) -> str:
    """Сжимает недавний контекст диалога для извлечения search-параметров."""
    if not history:
        return ""

    parts = []
    for msg in history:
        role = msg.get("role")
        content = (msg.get("content") or "").strip()
        if not content or role not in {"user", "assistant", "system"}:
            continue
        parts.append(f"{role}: {content}")

    limit = _router_history_context_limit()
    selected = []
    total = 0
    for part in reversed(parts):
        part_size = len(part) + (1 if selected else 0)
        if selected and total + part_size > limit:
            break
        if not selected and part_size > limit:
            selected.append(part[-limit:].lstrip())
            break
        selected.append(part)
        total += part_size
    return "\n".join(reversed(selected))


def _router_history_context_limit() -> int:
    raw = os.getenv("ROUTER_CONTEXT_CHAR_LIMIT", "2500")
    try:
        value = int(raw)
    except ValueError:
        return 2500
    return max(value, 800)


def _build_router_prompt(user_query: str, history_context: str, current_state: dict) -> str:
    """Строит prompt для маршрутизации: search / consultation / off_topic / conversation."""
    history_block = ""
    if history_context.strip():
        history_block = f"\nКонтекст:\n{history_context}\n"

    state_block = ""
    if current_state:
        state_block = f"\nState:\n{json.dumps(current_state, ensure_ascii=False)}\n"

    return f"""Guitar router. JSON only.
Keys: intent,enough_for_search,missing_fields,search_params,should_offer_search; optional current_turn_search,no_preference_fields,budget_default_offer,default_actions,state_action.
Intents: search,consultation,off_topic,conversation.
search_params: search_queries,price_min,price_max,type,brand,pickups,sound,style. RUB 100=1USD.
Ready search: enough=true,current_turn_search=true, final snapshot only, 1-3 title-searchable queries, explicit price, explicit type or "any". No stale state/history search.
Types: stratocaster,telecaster,les paul,sg,superstrat,acoustic,classical,bass,seven_string,any.
Not ready search: enough=false, missing_fields only budget/type. Type not important => type="any", no_preference_fields ["type"]. Unknown budget stays not ready; use budget_default_offer if relevant.
conversation: short conversational/meta turn with no guitar advice, result comparison, or catalog search. search_params=null, missing_fields=[], enough=false, should_offer_search=false. No subtypes/action labels/language flags.
consultation: guitar advice/explanation or comparison of latest numbered results without asking for new catalog variants. off_topic: unrelated.
Search if current message asks start/continue/broaden/narrow/change catalog search ("покажи ещё", cheaper, links, budget/type change). Style/language meta plus search change is still search; answer language is handled later. New search reset; follow-up patch full snapshot.

Examples:
Q:"хочу гитару, я новичок, ничего не понимаю, без лишних вопросов"
A:{{"intent":"search","enough_for_search":true,"missing_fields":[],"current_turn_search":true,"no_preference_fields":["type"],"default_actions":["apply_beginner_budget"],"state_action":"reset","search_params":{{"search_queries":["Yamaha Pacifica"],"price_max":500,"type":"any"}},"should_offer_search":false}}
State price_max=500,type=any Q:"до 1000"
A:{{"intent":"search","enough_for_search":true,"missing_fields":[],"current_turn_search":true,"state_action":"patch","search_params":{{"search_queries":["Yamaha Pacifica"],"price_max":1000,"type":"any"}},"should_offer_search":false}}
State missing_fields=["budget","type"],asked_fields=["budget","type"] Q:"не принципиально"
A:{{"intent":"search","enough_for_search":false,"missing_fields":["budget"],"no_preference_fields":["type"],"state_action":"patch","search_params":{{"type":"any"}},"should_offer_search":false}}
State ready search Q:"can you answer in english?"
A:{{"intent":"conversation","enough_for_search":false,"missing_fields":[],"search_params":null,"should_offer_search":false}}
State ready search Q:"amazing"
A:{{"intent":"conversation","enough_for_search":false,"missing_fields":[],"search_params":null,"should_offer_search":false}}
State ready search Q:"спасибо, теперь до 700"
A:{{"intent":"search","enough_for_search":true,"missing_fields":[],"current_turn_search":true,"state_action":"patch","search_params":{{"search_queries":["Yamaha Pacifica"],"price_max":700,"type":"any"}},"should_offer_search":false}}
State ready search Q:"can you answer in english and show cheaper ones?"
A:{{"intent":"search","enough_for_search":true,"missing_fields":[],"current_turn_search":true,"state_action":"patch","search_params":{{"search_queries":["Yamaha Pacifica"],"price_max":500,"type":"any"}},"should_offer_search":false}}
Context: Последняя поисковая выдача Q:"чем 1ый лучше 2го"
A:{{"intent":"consultation","enough_for_search":false,"missing_fields":[],"search_params":null,"should_offer_search":false}}
{history_block}
{state_block}
Q:{user_query}
A:"""


def _build_router_repair_prompt(
    user_query: str,
    history_context: str,
    current_state: dict,
    invalid_plan: dict,
    validation_errors: list[str],
) -> str:
    """Строит компактный prompt для исправления JSON router без ответа пользователю."""
    history_block = ""
    if history_context.strip():
        history_block = f"\nContext:\n{history_context}\n"

    state_block = ""
    if current_state:
        state_block = f"\nState:\n{json.dumps(current_state, ensure_ascii=False)}\n"

    invalid_json = json.dumps(invalid_plan, ensure_ascii=False, default=str)
    errors_json = json.dumps(validation_errors or [], ensure_ascii=False)

    return f"""Ты исправляешь JSON LLM-router для сервиса подбора гитар.
Не отвечай пользователю. Верни только исправленный JSON той же формы.
Не придумывай объявления, ссылки, магазины, цены или наличие.
Используй исходный запрос, context и state.
For ready search, return the final effective search_params snapshot. backend will not apply default_actions or stale state.
Short conversational/meta turns => search_params=null, missing_fields=[], enough_for_search=false. Do not repair these into stale ready search.
Ready search must include current_turn_search=true when the current user message itself asks to start, continue, broaden, narrow, or otherwise change a catalog search.
Do not introduce conversation subtypes, language flags, or search action enums during repair.
Если default_actions содержит apply_beginner_budget/accept_beginner_budget, поставь фактическое число в search_params.price_max.
Если user changed a constraint, reflect it in search_params.
Если intent=search и enough_for_search=true: search_queries 1-3 непустые строки, price_max/price_min явный, type явный или "any".
Если бюджет неизвестен, не делай unlimited search: используй budget_default_offer, not ready search.
Если пользователь отвечает "не важно/не принципиально/любой" на уточнение type, закрой type как "any", но оставь missing_fields ["budget"], если бюджет всё ещё неизвестен.
consultation/off_topic/conversation => search_params=null. off_topic/conversation => should_offer_search=false.

Форма:
{{"intent":"search|consultation|off_topic|conversation","enough_for_search":true|false,"missing_fields":["budget","type"],"current_turn_search":true|false,"no_preference_fields":[],"budget_default_offer":false,"default_actions":[],"state_action":"patch|reset","search_params":{{"search_queries":["..."],"price_min":null,"price_max":1200,"type":null,"brand":null,"pickups":null,"sound":null,"style":null}}|null,"should_offer_search":true|false}}
{history_block}
{state_block}
User query:
{user_query}

Validation errors:
{errors_json}

Invalid JSON:
{invalid_json}

Corrected JSON:"""


def _build_router_recovery_prompt(
    user_query: str,
    history_context: str,
    current_state: dict,
    invalid_plan: dict,
    validation_errors: list[str],
) -> str:
    """Строит prompt для safe UX recovery после невалидного router/repair JSON."""
    history_block = ""
    if history_context.strip():
        history_block = f"\nContext:\n{history_context}\n"

    state_block = ""
    if current_state:
        state_block = f"\nState:\n{json.dumps(current_state, ensure_ascii=False)}\n"

    invalid_json = json.dumps(invalid_plan, ensure_ascii=False, default=str)
    errors_json = json.dumps(validation_errors or [], ensure_ascii=False)

    return f"""Ты восстанавливаешь UX-маршрут после невалидного JSON LLM-router для сервиса подбора гитар.
Не отвечай пользователю текстом. Верни только JSON router contract.

Цель: не запускать небезопасный поиск, а вернуть понятный следующий шаг.
Запрещено возвращать enough_for_search=true.
If invalid JSON tried to run search for a short conversational/meta turn, recover as conversation, not clarification.
If ready search has no current_turn_search=true grounded in the current user message, recover as conversation or clarification, not stale search.
Do not introduce conversation subtypes, language flags, or search action enums during recovery.
Если пользователь закрыл часть уточнений, обнови search_params и missing_fields.
Если пользователь говорит "не важно", "не принципиально", "любой", "без разницы" про тип инструмента, поставь type="any" и no_preference_fields ["type"].
Если бюджет неизвестен, missing_fields должен содержать "budget"; не придумывай цену.
Если тип неизвестен и пользователь не отказался выбирать тип, missing_fields должен содержать "type".
Если запрос консультационный, нерелевантный или conversational/meta, верни consultation/off_topic/conversation с search_params=null.

Форма:
{{"intent":"search|consultation|off_topic|conversation","enough_for_search":false,"missing_fields":["budget","type"],"current_turn_search":false,"no_preference_fields":[],"budget_default_offer":false,"default_actions":[],"state_action":"patch|reset","search_params":{{"search_queries":[],"price_min":null,"price_max":null,"type":null,"brand":null,"pickups":null,"sound":null,"style":null}}|null,"should_offer_search":false}}
{history_block}
{state_block}
User query:
{user_query}

Validation errors:
{errors_json}

Invalid JSON:
{invalid_json}

Recovered safe JSON:"""
