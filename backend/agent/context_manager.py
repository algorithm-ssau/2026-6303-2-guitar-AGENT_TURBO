"""Модуль управления контекстом диалога."""
import os
from backend.history.service import get_session_messages
from backend.utils.logger import get_logger

logger = get_logger("agent.context_manager")

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
        
        history = []
        for item in items:
            history.append({"role": "user", "content": item["user_query"]})
            if item.get("mode") == "search" and item.get("results"):
                parts = ["Я нашёл следующие гитары:"]
                for r in item["results"]:
                    title = r.get("title", "")
                    price = r.get("price", "")
                    parts.append(f"- {title}, ${price}")
                answer = "\n".join(parts)
            else:
                answer = item.get("answer") or ""
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
