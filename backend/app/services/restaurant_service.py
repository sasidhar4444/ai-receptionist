"""Restaurant information service — structured DB lookups for exact facts."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Restaurant, RestaurantHour, RestaurantPolicy, MenuItem
from app.config.logging import logger


async def get_restaurant_info(db: AsyncSession, restaurant_id: int) -> dict:
    """Return basic restaurant info."""
    result = await db.execute(
        select(Restaurant).where(Restaurant.id == restaurant_id)
    )
    r = result.scalars().first()
    if not r:
        return {"success": False, "error_code": "RESTAURANT_NOT_FOUND"}

    return {
        "success": True,
        "id": r.id,
        "name": r.name,
        "address": r.address,
        "phone": r.phone,
        "description": r.description,
        "timezone": r.timezone,
    }


async def get_hours(db: AsyncSession, restaurant_id: int) -> dict:
    """Return all opening hours as structured data."""
    result = await db.execute(
        select(RestaurantHour)
        .where(RestaurantHour.restaurant_id == restaurant_id)
        .order_by(RestaurantHour.id)
    )
    hours = result.scalars().all()
    return {
        "success": True,
        "hours": [
            {
                "day_of_week": h.day_of_week,
                "open_at": str(h.open_at) if h.open_at else None,
                "close_at": str(h.close_at) if h.close_at else None,
                "is_closed": h.is_closed,
            }
            for h in hours
        ],
    }


async def get_policy(db: AsyncSession, restaurant_id: int, key: str) -> dict:
    """Return a specific restaurant policy by key."""
    result = await db.execute(
        select(RestaurantPolicy).where(
            RestaurantPolicy.restaurant_id == restaurant_id,
            RestaurantPolicy.key == key,
        )
    )
    policy = result.scalars().first()
    if not policy:
        return {"success": True, "found": False}
    return {"success": True, "found": True, "key": policy.key, "value": policy.value}


async def get_menu(db: AsyncSession, restaurant_id: int, category: str | None = None) -> dict:
    """Return menu items, optionally filtered by category."""
    query = select(MenuItem).where(
        MenuItem.restaurant_id == restaurant_id,
        MenuItem.is_available == True,  # noqa: E712
    )
    if category:
        query = query.where(MenuItem.category == category)

    result = await db.execute(query.order_by(MenuItem.category, MenuItem.name))
    items = result.scalars().all()

    return {
        "success": True,
        "items": [
            {
                "name": i.name,
                "category": i.category,
                "description": i.description,
                "price": i.price,
                "allergens": i.allergens,
                "is_vegetarian": i.is_vegetarian,
                "is_vegan": i.is_vegan,
            }
            for i in items
        ],
    }
