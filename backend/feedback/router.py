from fastapi import APIRouter, Depends
from backend.auth.dependencies import get_current_user
from backend.auth.service import UserRecord
from backend.history.service import ensure_session_owner
from .models import FeedbackRequest, FeedbackStats
from .service import save_feedback, get_feedback_stats

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

@router.post("/", response_model=dict)
def create_feedback(req: FeedbackRequest, current_user: UserRecord = Depends(get_current_user)):
    ensure_session_owner(req.session_id, current_user["id"])
    row_id = save_feedback(req)
    return {"id": row_id}

@router.get("/stats", response_model=FeedbackStats)
def get_stats(current_user: UserRecord = Depends(get_current_user)):
    return get_feedback_stats(user_id=current_user["id"])
