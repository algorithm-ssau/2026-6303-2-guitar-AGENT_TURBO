"""Exceptions for the agent module."""
import re
from typing import Optional

class LLMUnavailableError(RuntimeError):
    """LLM недоступна или не смогла обработать обязательный вызов."""

    def __init__(self, message: str, user_message: Optional[str] = None):
        super().__init__(message)
        self.user_message = user_message or _safe_llm_unavailable_message(message)


class InvalidRouterResponseError(RuntimeError):
    """LLM-router вернул невалидный JSON/shape."""


def _safe_llm_unavailable_message(error: object) -> str:
    """Возвращает безопасное пользовательское описание причины LLM-сбоя."""
    text = str(error or "")
    lowered = text.lower()
    if "rate_limit" in lowered or "rate limit" in lowered or "tokens per day" in lowered or "tpd" in lowered:
        retry_match = re.search(r"try again in ([0-9dhms. ]+)", text, flags=re.IGNORECASE)
        if retry_match:
            retry_after = retry_match.group(1).strip().rstrip(".")
            return f"Лимит LLM на сегодня исчерпан. Попробуйте снова примерно через {retry_after}."
        return "Лимит LLM на сегодня исчерпан. Попробуйте повторить запрос позже."
    if "request_too_large" in lowered or "request entity too large" in lowered or "413" in lowered:
        return "Не получилось обработать этот запрос через LLM. Попробуйте переформулировать последний вопрос."
    return "Сервис временно недоступен: не удалось обработать запрос через LLM."
