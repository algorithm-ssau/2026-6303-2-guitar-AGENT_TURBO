from fastapi import APIRouter, Depends, HTTPException
from backend.auth.dependencies import get_current_user
from backend.auth.service import UserRecord
from backend.search.models import ChatRequest, ChatResponse
from backend.agent.service import (
    InvalidRouterResponseError,
    LLMUnavailableError,
    interpret_query,
)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserRecord = Depends(get_current_user),
) -> ChatResponse:
    """
    Обработка запроса пользователя через LLM-пайплайн.

    Принимает текстовый запрос, вызывает interpret_query для анализа,
    возвращает ответ в режиме 'search' (с результатами) или 'consultation' (текстовый ответ).
    """
    try:
        result = interpret_query(text=request.query)
    except LLMUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail=exc.user_message,
        ) from exc
    except InvalidRouterResponseError as exc:
        raise HTTPException(
            status_code=502,
            detail="Некорректный ответ LLM-router.",
        ) from exc

    if result["mode"] == "search":
        return ChatResponse(
            mode="search",
            results=result.get("results", []),
            search_params=result.get("search_params"),
        )
    if result["mode"] == "clarification":
        return ChatResponse(
            mode="clarification",
            question=result.get("question", ""),
            search_params=result.get("search_params"),
        )
    return ChatResponse(
        mode="consultation",
        answer=result.get("answer", ""),
        debug_think=result.get("debug_think"),
    )
