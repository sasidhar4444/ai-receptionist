"""
Tool: find_available_table
Checks live table availability in PostgreSQL. Never invents availability.
"""
import time
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import logger
from app.services import table_service


class TableAvailabilityInput(BaseModel):
    party_size: int = Field(..., ge=1, le=20, description="Number of guests in the party")
    zone: Optional[str] = Field(None, description="Preferred seating zone: indoor, outdoor, private, or any")


class TableAvailabilityOutput(BaseModel):
    success: bool
    available: Optional[bool] = None
    table_id: Optional[int] = None
    table_number: Optional[int] = None
    capacity: Optional[int] = None
    zone: Optional[str] = None
    error_code: Optional[str] = None


async def execute_find_available_table(
    db: AsyncSession,
    restaurant_id: int,
    input_data: TableAvailabilityInput,
) -> dict:
    """
    Executes table search with server-side validation, timing, and error handling.
    """
    start_time = time.monotonic()
    tool_name = "find_available_table"

    try:
        result = await table_service.find_available_table(
            db=db,
            restaurant_id=restaurant_id,
            party_size=input_data.party_size,
            zone=input_data.zone,
        )
        latency_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "tool_executed",
            tool=tool_name,
            success=result.get("success", False),
            latency_ms=latency_ms,
        )
        return result
    except Exception as exc:
        latency_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("tool_execution_failed", tool=tool_name, error=str(exc), latency_ms=latency_ms)
        return {
            "success": False,
            "available": False,
            "error_code": "TABLE_LOOKUP_FAILED",
        }
