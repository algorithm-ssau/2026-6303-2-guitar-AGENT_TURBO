"""Модуль генерации пояснений к результатам поиска."""
import logging
from backend.agent.llm_client import LLMClient

logger = logging.getLogger(__name__)

EXPLANATION_PROMPT = """Напиши 1–2 предложения почему эти гитары подходят под запрос: {query}. Без списков, только текст."""

def generate_explanation(query: str, results: list, llm_client: LLMClient) -> str:
    """Генерирует краткое пояснение почему результаты подходят под запрос."""
    if not llm_client or not results:
        return ""

    try:
        models = ", ".join([r.get("title", "") for r in results[:3] if isinstance(r, dict)])
        if not models:
            return ""

        user_message = f"Запрос: {query}\nНайденные гитары: {models}"
        prompt = EXPLANATION_PROMPT.format(query=query)
        
        explanation = llm_client.ask(user_message, prompt)
        return explanation.strip()
    except Exception as e:
        logger.error("Ошибка при генерации пояснения: %s", e)
        return ""
