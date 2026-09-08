"""Table service — queries live PostgreSQL table state. Never invents availability."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RestaurantTable, TableStatus
from app.config.logging import logger


async def get_all_tables(db: AsyncSession, restaurant_id: int) -> list[dict]:
    """Return all tables with their current live status."""
    result = await db.execute(
        select(RestaurantTable)
        .where(RestaurantTable.restaurant_id == restaurant_id)
        .order_by(RestaurantTable.table_number)
    )
    tables = result.scalars().all()
    return [
        {
            "id": t.id,
            "table_number": t.table_number,
            "capacity": t.capacity,
            "zone": t.zone,
            "status": t.status,
        }
        for t in tables
    ]


async def find_available_table(
    db: AsyncSession,
    restaurant_id: int,
    party_size: int,
    zone: Optional[str] = None,
) -> dict:
    """
    Find the best available table for a given party size.

    Returns:
        { success, available, table_number, capacity, zone }
        or { success, available: False }
        or { success: False, error_code } on DB error.

    The LLM must use ONLY this result — never invent availability.
    """
    try:
        query = (
            select(RestaurantTable)
            .where(
                RestaurantTable.restaurant_id == restaurant_id,
                RestaurantTable.capacity >= party_size,
                RestaurantTable.status.in_([
                    TableStatus.AVAILABLE, TableStatus.READY
                ]),
            )
            .order_by(RestaurantTable.capacity)  # smallest suitable table first
        )

        if zone and zone.lower() != "any":
            query = query.where(RestaurantTable.zone == zone.lower())

        result = await db.execute(query)
        table = result.scalars().first()

        if table:
            logger.info(
                "table_found",
                party_size=party_size,
                table_number=table.table_number,
                zone=table.zone,
            )
            return {
                "success": True,
                "available": True,
                "table_id": table.id,
                "table_number": table.table_number,
                "capacity": table.capacity,
                "zone": table.zone,
            }

        logger.info("no_table_available", party_size=party_size, zone=zone)
        return {"success": True, "available": False}

    except Exception as exc:
        logger.error("table_service_error", error=str(exc))
        return {"success": False, "error_code": "DATABASE_UNAVAILABLE"}
