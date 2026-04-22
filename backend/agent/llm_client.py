"""КЛИЕНТ GROQ LLM"""
import json
import os
from typing import Optional

from groq import Groq
from backend.agent.param_extractor import (
    build_search_prompt,
    extract_json_dict_from_text,
    extract_params_from_llm_response,
)

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        self.client = Groq(api_key=self.api_key)
        self.model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

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
                model=self.model,
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
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": transcript}
                ],
                temperature=0.0
            )
            return response.choices[0].message.content
        except Exception:
            return ""

    def extract_search_params(self, user_message: str, history: Optional[list] = None) -> dict:
        mapping_path = os.path.join(os.path.dirname(__file__), "../../docs/MAPPING.md")
        mapping_table = ""
        if os.path.exists(mapping_path):
            with open(mapping_path, "r", encoding="utf-8") as f:
                mapping_table = f.read()

        prompt = build_search_prompt(
            user_message,
            mapping_table,
            _format_history_for_search(history),
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return extract_params_from_llm_response(content)
        except Exception:
            return extract_params_from_llm_response("invalid")

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

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            if isinstance(content, str):
                try:
                    direct = json.loads(content)
                    if isinstance(direct, dict):
                        return direct
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
                parsed = extract_json_dict_from_text(content)
                if parsed is not None:
                    return parsed
            return {}
        except Exception:
            return {}


def get_llm_client():
    """Compatibility wrapper for service.py"""
    return LLMClient().client

def get_llm_model():
    return os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")


def _format_history_for_search(history: Optional[list]) -> str:
    """Сжимает недавний контекст диалога для извлечения search-параметров."""
    if not history:
        return ""

    parts = []
    for msg in history[-6:]:
        role = msg.get("role")
        content = (msg.get("content") or "").strip()
        if not content or role not in {"user", "assistant", "system"}:
            continue
        parts.append(f"{role}: {content}")

    return "\n".join(parts)


def _build_router_prompt(user_query: str, history_context: str, current_state: dict) -> str:
    """Строит prompt для маршрутизации: search / consultation / clarification."""
    history_block = ""
    if history_context.strip():
        history_block = f"\nКонтекст диалога:\n{history_context}\n"

    state_block = ""
    if current_state:
        state_block = f"\nТекущее структурированное состояние сессии:\n{json.dumps(current_state, ensure_ascii=False)}\n"

    return f"""Ты определяешь, что делать с запросом пользователя в сервисе подбора гитар.

Тебе нужно вернуть ТОЛЬКО JSON.

Правила:
1. Если пользователь хочет подобрать инструмент, увидеть варианты, получить ссылки или подтверждает готовность посмотреть варианты, это intent='search'.
2. Если для подбора уже достаточно данных, ставь enough_for_search=true.
3. Если данных для подбора не хватает, ставь intent='search', enough_for_search=false и перечисли missing_fields.
4. Если пользователь задаёт теоретический вопрос без запроса на подбор, ставь intent='consultation'.
5. В consultation_answer НЕЛЬЗЯ указывать внешние магазины, домены, маркетплейсы, конкретные ссылки и выдуманные товарные примеры.
6. Если после консультации уместно предложить реальные варианты с Reverb, ставь should_offer_search=true.
7. Если из контекста уже ясно, что пользователь говорит 'да', 'давай', 'хочу', 'покажи', 'дай ссылки' про ранее обсуждавшийся подбор, используй контекст и верни search.
8. Если в structured state уже есть тип/бюджет, не забывай их. Новое сообщение дополняет или уточняет state, а не обнуляет его.
9. Если пользователь пишет, что тип ему не важен ('не важно', 'все равно', 'любой'), это НЕ missing field. В search_params.type верни 'any'.

Допустимые missing_fields: budget, type.

Верни JSON строго такой формы:
{{
  "intent": "search" | "consultation",
  "enough_for_search": true | false,
  "missing_fields": ["budget", "type"],
  "search_params": {{
    "search_queries": ["Fender Stratocaster"],
    "price_min": null,
    "price_max": 1200,
    "type": "Stratocaster",
    "brand": "Fender",
    "pickups": null,
    "sound": "bright"
  }} | null,
  "consultation_answer": "строка",
  "should_offer_search": true | false
}}
{history_block}
{state_block}
Текущий запрос пользователя:
{user_query}

Верни только JSON без пояснений."""
