"""Pydantic-модели для WebSocket сообщений и результатов поиска."""

from pydantic import BaseModel
from typing import List, Optional, Literal

# Используем модели из search.models с поддержкой camelCase
from backend.search.models import GuitarResult


class WSMessage(BaseModel):
    """Модель сообщения WebSocket."""
    type: Literal["status", "result", "error"]
    mode: Optional[Literal["search", "consultation", "clarification"]] = None
    status: Optional[str] = None
    answer: Optional[str] = None
    question: Optional[str] = None
    results: Optional[List[GuitarResult]] = None
    question: Optional[str] = None
    explanation: Optional[str] = None
    search_params: Optional[dict] = None
    session_id: Optional[int] = None
