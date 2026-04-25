from pydantic import BaseModel
from typing import Literal, Optional

class FeedbackRequest(BaseModel):
    session_id: int
    guitar_id: str
    rating: Literal["up", "down"]
    query: Optional[str] = None

class FeedbackStats(BaseModel):
    total: int
    up: int
    down: int
    ratio: float
    by_guitar: dict[str, dict]