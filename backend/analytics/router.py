"""REST-эндпоинты для метрик пайплайна."""

from fastapi import APIRouter
from pydantic import BaseModel

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
async def metrics_health() -> KPIResponse:
    """Вернуть KPI пайплайна в формате API-контракта."""
    return KPIResponse(**snake_to_camel(compute_kpi()))
