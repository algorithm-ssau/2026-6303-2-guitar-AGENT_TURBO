"""Guardrails for filtering LLM outputs."""
import re
import os
import time
import json
from typing import Optional, Callable

from backend.agent.exceptions import InvalidRouterResponseError
from backend.history.service import strip_think_blocks


CATALOG_GUARDRAIL_ANSWER = (
    "Сейчас это выглядит как запрос на подбор, а не консультацию. "
    "Чтобы показать только реальные варианты из каталога со ссылками, "
    "напишите тип гитары и бюджет, например: `Stratocaster до 1200$`."
)

MODEL_BRANDS = (
    "Fender", "Squier", "Gibson", "Epiphone", "Ibanez", "Jackson", "PRS",
    "Yamaha", "ESP", "Schecter", "Gretsch", "Charvel", "Cort", "G&L",
)


def sanitize_consultation_answer(answer: str, allowed_titles: Optional[list[str]] = None) -> str:
    """Блокирует ответы консультации, похожие на каталог или ссылки."""
    text, reason = sanitize_consultation_answer_result(answer, allowed_titles=allowed_titles)
    return CATALOG_GUARDRAIL_ANSWER if reason else text


def sanitize_consultation_answer_result(
    answer: str,
    allowed_titles: Optional[list[str]] = None,
) -> tuple[str, Optional[str]]:
    """Возвращает очищенный consultation answer или typed block reason."""
    text = (answer or "").strip()
    if not text:
        return text, None

    if looks_like_catalog_content(text, allowed_titles=allowed_titles):
        return "", "catalog_content"

    return text, None


def extract_think_block(answer: str) -> tuple[str, Optional[str]]:
    """Отделяет Qwen-style <think>...</think> от видимого ответа."""
    text = str(answer or "")
    matches = list(re.finditer(r"<think>(.*?)</think>", text, flags=re.IGNORECASE | re.DOTALL))
    if not matches:
        if re.search(r"<think>", text, flags=re.IGNORECASE):
            visible = strip_think_blocks(text) or ""
            debug = re.split(r"<think>", text, maxsplit=1, flags=re.IGNORECASE)[-1].strip()
            return visible, debug or None
        return text.strip(), None

    debug_parts = [match.group(1).strip() for match in matches if match.group(1).strip()]
    visible = re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    debug_think = "\n\n".join(debug_parts).strip() or None
    return visible, debug_think


def compact_llm_visible_text(text: object, limit: int) -> str:
    """Готовит короткий visible snippet для router context."""
    visible = strip_think_blocks(str(text or "")) or ""
    visible = re.sub(r"\s+", " ", visible).strip()
    if limit > 0 and len(visible) > limit:
        return f"{visible[:limit].rstrip()}..."
    return visible


def sanitize_off_topic_answer(answer: str) -> str:
    """Строгий guardrail для LLM-generated off-topic refusal."""
    text = (answer or "").strip()
    lowered = text.lower()
    if not text:
        raise InvalidRouterResponseError("off-topic LLM answer is empty")
    if contains_external_link_or_shop(lowered):
        raise InvalidRouterResponseError("off-topic LLM answer contains links or shops")
    if "```" in text or re.search(r"(^|\n)\s*(?:[-*]|\d+[.)])\s+", text):
        raise InvalidRouterResponseError("off-topic LLM answer contains code or list")
    if re.search(r"\b(def|class|import|for|while)\s+[A-Za-z_]", text):
        raise InvalidRouterResponseError("off-topic LLM answer appears to answer the coding task")
    return text


def sanitize_clarification_question(question: str) -> str:
    """Guardrail для LLM-generated clarification: только короткий вопрос/подтверждение."""
    text = (question or "").strip()
    if not text:
        raise InvalidRouterResponseError("clarification LLM answer is empty")
    lowered = text.lower()
    if contains_external_link_or_shop(lowered):
        raise InvalidRouterResponseError("clarification LLM answer contains links or shops")
    if "```" in text or re.search(r"(^|\n)\s*(?:[-*]|\d+[.)])\s+", text):
        raise InvalidRouterResponseError("clarification LLM answer contains code or list")
    if looks_like_catalog_content(text, allowed_titles=[]):
        raise InvalidRouterResponseError("clarification LLM answer contains catalog content")
    return text


def sanitize_conversation_answer(answer: str) -> str:
    """Guardrail for short conversational answers."""
    text = (answer or "").strip()
    lowered = text.lower()
    if not text:
        raise InvalidRouterResponseError("conversation LLM answer is empty")
    if contains_external_link_or_shop(lowered):
        raise InvalidRouterResponseError("conversation LLM answer contains links or shops")
    if "```" in text or re.search(r"(^|\n)\s*(?:[-*]|\d+[.)])\s+", text):
        raise InvalidRouterResponseError("conversation LLM answer contains code or list")
    if looks_like_catalog_content(text, allowed_titles=[]):
        raise InvalidRouterResponseError("conversation LLM answer contains catalog content")
    return text


def contains_external_link_or_shop(lowered: str) -> bool:
    if re.search(r"https?://|www\.|\b[a-z0-9-]+\.(com|ru|net|org)\b", lowered):
        return True
    if re.search(r"\b(reverb|amazon|sweetwater|guitarcenter|musician'?s friend)\b", lowered):
        return True
    return False


def looks_like_catalog_content(text: str, allowed_titles: Optional[list[str]] = None) -> bool:
    """Определяет, что LLM начал перечислять товары, магазины или ссылки."""
    lowered = text.lower()

    if contains_external_link_or_shop(lowered):
        return True

    if "ссылка на пример" in lowered or "примеры телекастеров" in lowered:
        return True

    branded_models = extract_branded_model_mentions(text)
    if not branded_models:
        return False

    allowed = [normalize_model_text(title) for title in (allowed_titles or []) if str(title or "").strip()]
    if not allowed:
        return True

    uncovered = [
        mention for mention in branded_models
        if not is_allowed_model_mention(normalize_model_text(mention), allowed)
    ]
    return bool(uncovered)


def extract_branded_model_mentions(text: str) -> list[str]:
    brands = "|".join(re.escape(brand) for brand in MODEL_BRANDS)
    pattern = re.compile(
        rf"\b(?:{brands})\b(?:\s+[A-Z0-9][A-Za-z0-9'&./+-]*){{1,7}}",
        re.IGNORECASE,
    )
    mentions = []
    seen = set()
    for match in pattern.finditer(text):
        mention = match.group(0).strip(" ,.;:!?()[]{}")
        normalized = normalize_model_text(mention)
        if len(normalized.split()) < 2 or normalized in seen:
            continue
        mentions.append(mention)
        seen.add(normalized)
    return mentions


def normalize_model_text(text: str) -> str:
    lowered = str(text or "").lower()
    lowered = re.sub(r"[^a-z0-9а-яё]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def is_allowed_model_mention(mention: str, allowed_titles: list[str]) -> bool:
    if not mention or len(mention.split()) < 2:
        return False
    return any(mention in title or title in mention for title in allowed_titles)


def maybe_append_search_offer(answer: str, should_offer_search: bool) -> str:
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
