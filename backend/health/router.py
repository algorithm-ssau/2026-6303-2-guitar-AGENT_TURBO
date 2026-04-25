"""REST-эндпоинты для проверки состояния приложения."""

import os
import sqlite3
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/api/health", tags=["health"])


class HealthResponse(BaseModel):
    """Ответ health-check эндпоинта."""

    status: Literal["ok", "degraded"]
    checks: dict[str, bool]
    version: str


def _env_flag(name: str, default: bool = False) -> bool:
    """Преобразует переменную окружения в bool."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _db_path() -> str:
    """Возвращает путь до SQLite-БД истории."""
    return os.getenv(
        "CHAT_DB_PATH",
        str(Path(__file__).resolve().parent.parent / "history" / "chat.db"),
    )


def _check_database() -> bool:
    """Проверяет доступность SQLite и простого запроса."""
    conn = None
    try:
        conn = sqlite3.connect(_db_path())
        conn.execute("SELECT 1")
        return True
    except sqlite3.Error:
        return False
    finally:
        if conn is not None:
            conn.close()


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Возвращает сводный статус приложения."""
    checks = {
        "database": _check_database(),
        "llm_configured": bool(os.getenv("GROQ_API_KEY")),
        "mock_mode": _env_flag("USE_MOCK_REVERB", default=False),
        "reverb_api_configured": bool(os.getenv("REVERB_API_TOKEN")),
    }
    status: Literal["ok", "degraded"] = "ok"
    if not checks["database"] or not checks["llm_configured"]:
        status = "degraded"

    return HealthResponse(
        status=status,
        checks=checks,
        version="0.7.0",
    )


@router.get("/ping")
async def ping() -> dict[str, bool]:
    """Простой liveness-check."""
    return {"pong": True}
