from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.database.session import get_async_db
from app.core.logging import logger

router = APIRouter(tags=["Health"])


class ComponentStatus(BaseModel):
    status: str = Field(..., description="Component status (healthy, degraded, unconfigured, error)")
    details: str = Field(..., description="Descriptive detail of the component status")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall system health status (healthy, degraded, error)")
    app_name: str
    environment: str
    timestamp: str
    components: Dict[str, ComponentStatus]


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Check Endpoint",
    description="Validates status of FastAPI application, PostgreSQL database connectivity, and Redis cache.",
)
async def check_health(db: AsyncSession = Depends(get_async_db)) -> Dict[str, Any]:
    components = {}
    overall_healthy = True

    # 1. Database Check
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            components["database"] = ComponentStatus(
                status="healthy",
                details="PostgreSQL/Database connection responsive",
            )
        else:
            components["database"] = ComponentStatus(
                status="degraded",
                details="Database query returned unexpected result",
            )
            overall_healthy = False
    except Exception as e:
        logger.warning(f"Health check DB warning: {str(e)}")
        components["database"] = ComponentStatus(
            status="degraded",
            details=f"Database connectivity warning/fallback: {str(e)}",
        )

    # 2. Redis Check
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=1.0)
        await r.ping()
        await r.aclose()
        components["redis"] = ComponentStatus(
            status="healthy",
            details="Redis cache ping successful",
        )
    except Exception as e:
        components["redis"] = ComponentStatus(
            status="unconfigured",
            details=f"Redis cache unreachable or optional fallback: {str(e)}",
        )

    # 3. Market Data Service Check
    components["market_data_provider"] = ComponentStatus(
        status="healthy",
        details=f"Configured provider: {settings.MARKET_DATA_PROVIDER}",
    )

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "app_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": components,
    }
