"""Direct tool and RAG API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.config.settings import settings
from app.tools.restaurant_information import (
    RestaurantInformationInput,
    execute_get_restaurant_information,
)
from app.services import rag_service

router = APIRouter(tags=["tools"])


class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


@router.post("/tools/restaurant-information")
async def api_restaurant_information(
    payload: RestaurantInformationInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Direct API endpoint for restaurant information knowledge tool.
    Uses pgvector semantic RAG search against verified restaurant documents.
    """
    return await execute_get_restaurant_information(db, settings.restaurant_id, payload)


@router.post("/rag/search")
async def api_rag_search(
    payload: RAGSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Direct semantic search endpoint over knowledge documents."""
    return await rag_service.search_knowledge(
        db=db,
        restaurant_id=settings.restaurant_id,
        query=payload.query,
    )
