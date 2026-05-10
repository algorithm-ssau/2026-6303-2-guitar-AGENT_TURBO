"""Pydantic-модели для WebSocket сообщений и результатов поиска."""

from pydantic import BaseModel
from typing import List, Optional, Literal


class GuitarResult(BaseModel):
    """Модель результата поиска гитары."""
    id: str
    title: str
    price: float
    currency: str
    image_url: str
    listing_url: str


class WSMessage(BaseModel):
    """Модель сообщения WebSocket."""
    type: Literal["status", "result", "error"]
    mode: Optional[Literal["search", "consultation", "clarification"]] = None
    status: Optional[str] = None
    answer: Optional[str] = None
    results: Optional[List[GuitarResult]] = None
    question: Optional[str] = None
    explanation: Optional[str] = None
    session_id: Optional[int] = None
