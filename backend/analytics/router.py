"""REST-эндпоинты для метрик пайплайна."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.auth.service import UserRecord
from backend.analytics.pipeline_metrics import compute_kpi
from backend.utils.serializer import snake_to_camel

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


class KPIResponse(BaseModel):
    totalSessions: int
    totalExchanges: int
    avgElapsedMs: float
    p95ElapsedMs: float
    avgMessagesToFirstSearch: float
    clarificationRate: float
    repeatSessionRate: float
    kpiMet: bool


@router.get("/health", response_model=KPIResponse)
async def metrics_health(current_user: UserRecord = Depends(get_current_user)) -> KPIResponse:
    """Вернуть KPI пайплайна в формате API-контракта."""
    return KPIResponse(**snake_to_camel(compute_kpi(user_id=current_user["id"])))
