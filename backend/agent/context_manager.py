"""Модуль управления контекстом диалога."""
import os
from backend.history.service import get_session_messages
from backend.history.service import strip_think_blocks
from backend.utils.logger import get_logger

logger = get_logger("agent.context_manager")

def format_search_results_context(results: list, latest: bool = True, limit: int = 5) -> str:
    """Форматирует сохранённую search-выдачу как numbered context для LLM."""
    label = "Последняя поисковая выдача:" if latest else "Предыдущая поисковая выдача:"
    parts = [label]
    for index, result in enumerate((results or [])[:limit], start=1):
        title = str(result.get("title") or "").strip()
        if not title:
            continue
        price = _format_price(result.get("price"))
        suffix = f", {price}" if price else ""
        parts.append(f"#{index} {title}{suffix}")
    return "\n".join(parts)


def _format_price(value: object) -> str:
    if value in (None, ""):
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        text = str(value).strip()
        return text if text.startswith("$") else f"${text}"
    if number.is_integer():
        return f"${int(number)}"
    return f"${number:.2f}".rstrip("0").rstrip(".")


def estimate_tokens(text: str) -> int:
    """Грубая оценка токенов: 1 токен ≈ 3 символа."""
    if not text:
        return 0
    return len(text) // 3

def build_context(
    session_id: int, 
    system_prompt: str, 
    current_query: str,
    llm_client = None
) -> list:
    """Формирует контекст для LLM с суммаризацией при необходимости."""
    if not session_id:
        return []
        
    try:
        items = get_session_messages(session_id)
        limit_str = os.getenv("MODEL_CONTEXT_LIMIT", "128000")
        try:
            limit = int(limit_str)
        except ValueError:
            limit = 128000
            
        threshold = int(limit * 0.75)
        
        latest_search_index = None
        for index, item in enumerate(items):
            if item.get("mode") == "search" and item.get("results"):
                latest_search_index = index

        history = []
        for index, item in enumerate(items):
            history.append({"role": "user", "content": item["user_query"]})
            if item.get("mode") == "search" and item.get("results"):
                answer = format_search_results_context(
                    item["results"],
                    latest=index == latest_search_index,
                )
            else:
                answer = strip_think_blocks(item.get("answer") or "") or ""
            history.append({"role": "assistant", "content": answer})
            
        # Считаем текущий размер
        current_len = sum(estimate_tokens(msg["content"]) for msg in history)
        current_len += estimate_tokens(system_prompt) + estimate_tokens(current_query)
        
        if current_len <= threshold or not llm_client:
            if not llm_client and current_len > threshold:
                return history[-10:]
            return history
            
        # Оставляем последние 3 пары (6 сообщений)
        recent = history[-6:] if len(history) >= 6 else history
        older = history[:-6] if len(history) >= 6 else []
        
        if not older:
            return history
            
        prompt = "Сделай краткое summary предыдущего диалога (ключевые предпочтения пользователя, его имя если представился, что он искал, что ему понравилось). До 200 слов."
        summary = llm_client.summarize(older, prompt)
        
        if not summary:
            return history[-10:]
            
        new_history = [{"role": "system", "content": summary}] + recent
        return new_history
        
    except Exception as e:
        logger.error("Ошибка при формировании контекста: %s", e)
        return []
