"""Restaurant info, menu, hours, and policies routes."""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.restaurant_service import (
    get_restaurant_info,
    get_menu,
    get_hours,
    get_policy,
)
from app.config.settings import settings

router = APIRouter(tags=["restaurant"])


@router.get("/restaurant")
async def restaurant_info(db: AsyncSession = Depends(get_db)):
    """Return basic restaurant information."""
    return await get_restaurant_info(db, settings.restaurant_id)


@router.get("/menu")
async def menu(category: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Return menu items, optionally filtered by category."""
    return await get_menu(db, settings.restaurant_id, category)


@router.get("/hours")
async def hours(db: AsyncSession = Depends(get_db)):
    """Return restaurant opening hours."""
    return await get_hours(db, settings.restaurant_id)


@router.get("/policy/{key}")
async def policy(key: str, db: AsyncSession = Depends(get_db)):
    """Return a specific restaurant policy."""
    return await get_policy(db, settings.restaurant_id, key)
