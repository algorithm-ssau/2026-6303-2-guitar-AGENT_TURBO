"""REST-эндпоинты для истории чата."""

from fastapi import APIRouter

from backend.history.models import (
    SessionsResponse, Session, CreateSessionRequest, CreateSessionResponse,
    HistoryResponse, HistoryItem, ClearResponse, StatsResponse,
)
from backend.history.service import (
    get_sessions, create_session, get_session_messages,
    delete_session, clear_history,
)
from backend.history.stats import get_stats

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/sessions", response_model=SessionsResponse)
async def list_sessions():
    """Получить список сессий (от новых к старым)."""
    sessions = get_sessions()
    return SessionsResponse(sessions=[Session(**s) for s in sessions])


@router.post("/sessions", response_model=CreateSessionResponse)
async def new_session(request: CreateSessionRequest):
    """Создать новую сессию."""
    session_id = create_session(request.title)
    return CreateSessionResponse(id=session_id)


@router.get("/sessions/{session_id}/messages", response_model=HistoryResponse)
async def session_messages(session_id: int):
    """Получить сообщения сессии."""
    items = get_session_messages(session_id)
    return HistoryResponse(items=[HistoryItem(**item) for item in items])


@router.delete("/sessions/{session_id}")
async def remove_session(session_id: int):
    """Удалить сессию."""
    delete_session(session_id)
    return {"ok": True}


@router.delete("/history", response_model=ClearResponse)
async def delete_all_history():
    """Очистить всю историю."""
    count = clear_history()
    return ClearResponse(deleted=count)


@router.get("/stats", response_model=StatsResponse)
async def get_usage_stats():
    """Получить статистику использования."""
    stats = get_stats()
    return StatsResponse(**stats)
