"""Сервис агента: точка входа для обработки пользовательских запросов."""

from backend.agent.mode_detector import detect_mode


def interpret_query(text: str, llm_client=None, search_fn=None) -> dict:
    """Обрабатывает запрос пользователя: определяет режим и вызывает нужную ветку.

    Args:
        text: текст запроса пользователя
        llm_client: callable для вызова LLM (принимает prompt, возвращает str)
        search_fn: callable для поиска гитар (принимает text, возвращает list)

    Returns:
        dict с ключами:
            - mode: "search" или "consultation"
            - answer: ответ LLM (для consultation)
            - results: результаты поиска (для search)
    """
    mode = detect_mode(text)

    if mode == "consultation":
        # Консультация — LLM отвечает напрямую, поиск не вызывается
        answer = ""
        if llm_client:
            answer = llm_client(text)
        return {"mode": "consultation", "answer": answer}

    # Поиск — вызываем поисковый пайплайн
    results = []
    if search_fn:
        results = search_fn(text)

    return {"mode": "search", "results": results}
