from fastapi import APIRouter

from backend.search.models import ChatRequest, ChatResponse
from backend.agent.service import interpret_query

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Обработка запроса пользователя через LLM-пайплайн.

    Принимает текстовый запрос, вызывает interpret_query для анализа,
    возвращает ответ в режиме 'search' (с результатами) или 'consultation' (текстовый ответ).
    """
    result = interpret_query(text=request.query)

    if result["mode"] == "search":
        return ChatResponse(
            mode="search",
            results=result.get("results", [])
        )
    else:
        return ChatResponse(
            mode="consultation",
            answer=result.get("answer", "")
        )
