from fastapi import APIRouter

from backend.search.models import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Обработка запроса пользователя.
    
    Принимает текстовый запрос, вызывает LLM-сервис для анализа,
    возвращает ответ в режиме 'search' (с результатами) или 'chat' (текстовый ответ).
    """
    # TODO: Интеграция с LLM-сервисом (Павлов)
    # Пока возвращаем заглушку
    return ChatResponse(
        mode="chat",
        answer=f"Получен запрос: {request.query}"
    )
