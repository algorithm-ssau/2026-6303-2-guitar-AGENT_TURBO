from fastapi import APIRouter
from .models import FeedbackRequest, FeedbackStats
from .service import save_feedback, get_feedback_stats

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

@router.post("/", response_model=dict)
def create_feedback(req: FeedbackRequest):
    row_id = save_feedback(req)
    return {"id": row_id}

@router.get("/stats", response_model=FeedbackStats)
def get_stats():
    return get_feedback_stats()