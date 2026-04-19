from fastapi import APIRouter
from ..agent.params_echo import parse_query_simple, format_params_for_display
from backend.search.models import ChatRequest, ChatResponse,ParseQueryResponse
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

@router.post("/query/parse", response_model=ParseQueryResponse)
async def parse_query(request: ChatRequest):
    # Никаких LLM и сайд-эффектов, только чистые регулярки
    params = parse_query_simple(request.query)
    formatted = format_params_for_display(params)
    return ParseQueryResponse(**formatted)