"""Pydantic-модели для API истории чата."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional, List, Dict


class Session(BaseModel):
    """Сессия чата."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: int
    title: str
    created_at: str
    updated_at: str


class SessionsResponse(BaseModel):
    """Ответ GET /api/sessions."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    sessions: List[Session]
    total: int


class CreateSessionRequest(BaseModel):
    """Запрос POST /api/sessions."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    title: str


class CreateSessionResponse(BaseModel):
    """Ответ POST /api/sessions."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: int


class HistoryItem(BaseModel):
    """Одна запись истории: пара запрос-ответ."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: int
    session_id: int
    user_query: str
    mode: str
    answer: Optional[str] = None
    results: Optional[List[dict]] = None
    created_at: str


class HistoryResponse(BaseModel):
    """Ответ GET /api/sessions/{id}/messages."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    items: List[HistoryItem]


class ClearResponse(BaseModel):
    """Ответ DELETE /api/history."""
    deleted: int


class StatsResponse(BaseModel):
    """Ответ GET /api/stats."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    total_sessions: int
    total_queries: int
    mode_distribution: Dict[str, int]
    avg_messages_per_session: float
    avg_queries_with_links: float
