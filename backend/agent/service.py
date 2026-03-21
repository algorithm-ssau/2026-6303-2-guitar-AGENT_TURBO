"""Сервис агента: точка входа для обработки пользовательских запросов."""

import json
import os
from backend.agent.llm_client import get_llm_client, get_llm_model

def get_system_prompt() -> str:
    """Загружает системный промпт из файла AGENT_PROMPT.md"""
    prompt_path = os.path.join(os.path.dirname(__file__), "../../docs/AGENT_PROMPT.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Ты ИИ-агент по подбору гитар. ВЕРНИ СТРОГО JSON."

def interpret_query(text: str, llm_client=None) -> dict:
    """Обрабатывает запрос пользователя через LLM.
    
    Возвращает JSON с ключами mode и params (для поиска) или answer (для консультации).
    """
    if llm_client is None:
        llm_client = get_llm_client()
        
    system_prompt = get_system_prompt()
    
    # Инструкция для LLM, чтобы гарантировать правильный JSON формат
    json_instruction = (
        "\n\nОБЯЗАТЕЛЬНО ВЕРНИ ОТВЕТ В ФОРМАТЕ JSON:\n"
        "Для поиска:\n"
        "{\"mode\": \"search\", \"params\": {\"search_queries\": [\"Fender Stratocaster\"], \"price_max\": 1000}}\n"
        "Для консультации:\n"
        "{\"mode\": \"consultation\", \"answer\": \"В чем разница...\"}"
    )
    
    messages = [
        {"role": "system", "content": system_prompt + json_instruction},
        {"role": "user", "content": text}
    ]
    
    try:
        response = llm_client.chat.completions.create(
            model=get_llm_model(),
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        # Fallback при ошибке парсинга или вызова
        return {"mode": "consultation", "answer": f"Извините, произошла ошибка обработки: {str(e)}"}
