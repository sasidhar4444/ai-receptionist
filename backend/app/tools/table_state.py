"""
Tool: get_live_table_state
Returns current statuses of all restaurant tables.
"""
import time
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import logger
from app.services import table_service


class TableStateItem(BaseModel):
    id: int
    table_number: int
    capacity: int
    zone: str
    status: str


class TableStateOutput(BaseModel):
    success: bool
    tables: List[TableStateItem] = []
    error_code: Optional[str] = None


async def execute_get_live_table_state(
    db: AsyncSession,
    restaurant_id: int,
) -> dict:
    """
    Retrieves all table statuses from PostgreSQL.
    """
    start_time = time.monotonic()
    tool_name = "get_live_table_state"

    try:
        tables = await table_service.get_all_tables(db, restaurant_id)
        latency_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "tool_executed",
            tool=tool_name,
            count=len(tables),
            success=True,
            latency_ms=latency_ms,
        )
        return {"success": True, "tables": tables}
    except Exception as exc:
        latency_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("tool_execution_failed", tool=tool_name, error=str(exc), latency_ms=latency_ms)
        return {"success": False, "tables": [], "error_code": "TABLE_STATE_FETCH_FAILED"}
