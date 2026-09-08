"""Health and liveness check routes."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Liveness and readiness check. Checks PostgreSQL connection.
    """
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "database": db_status,
        "service": "aria-restaurant-receptionist",
    }
