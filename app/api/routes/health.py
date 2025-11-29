"""
Health Check Endpoints
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.db.session import get_db
from app.models.schemas import HealthCheckResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthCheckResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint
    Returns service status and connectivity information
    """
    # Check database connection
    db_connected = False
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        pass

    # Redis check would go here
    redis_connected = False  # Placeholder

    return HealthCheckResponse(
        status="healthy" if db_connected else "degraded",
        version=__version__,
        timestamp=datetime.utcnow(),
        database_connected=db_connected,
        redis_connected=redis_connected,
    )


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Kubernetes readiness probe
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe
    """
    return {"status": "alive"}
