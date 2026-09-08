"""Table querying and live state API routes."""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.config.settings import settings
from app.services.table_service import get_all_tables
from app.tools.table_availability import (
    TableAvailabilityInput,
    execute_find_available_table,
)
from app.tools.table_state import execute_get_live_table_state

router = APIRouter(tags=["tables"])


@router.get("/tables")
async def list_tables(db: AsyncSession = Depends(get_db)):
    """Return all tables with their current live status."""
    tables = await get_all_tables(db, settings.restaurant_id)
    return {"tables": tables}


@router.post("/tools/find-available-table")
async def api_find_available_table(
    payload: TableAvailabilityInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Direct API endpoint for the find_available_table tool.
    Never invents availability — queries PostgreSQL directly.
    """
    return await execute_find_available_table(db, settings.restaurant_id, payload)


@router.post("/tools/table-state")
async def api_table_state(db: AsyncSession = Depends(get_db)):
    """Direct API endpoint for live table states."""
    return await execute_get_live_table_state(db, settings.restaurant_id)
