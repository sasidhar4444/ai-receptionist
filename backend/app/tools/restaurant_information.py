"""
Tool: get_restaurant_information
Retrieves verified facts from knowledge base (RAG via pgvector) and structured records.
Anti-hallucination rule: If found=false, the caller must never fabricate an answer.
"""
import time
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import logger
from app.services import rag_service, restaurant_service


class RestaurantInformationInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="The customer's question")


class KnowledgeSourceItem(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    score: Optional[float] = None


class RestaurantInformationOutput(BaseModel):
    success: bool
    found: bool
    sources: List[KnowledgeSourceItem] = []
    error_code: Optional[str] = None


async def execute_get_restaurant_information(
    db: AsyncSession,
    restaurant_id: int,
    input_data: RestaurantInformationInput,
) -> dict:
    """
    Executes semantic RAG query with server-side validation, timing, and error handling.
    """
    start_time = time.monotonic()
    tool_name = "get_restaurant_information"

    try:
        result = await rag_service.search_knowledge(
            db=db,
            restaurant_id=restaurant_id,
            query=input_data.query,
        )
        latency_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "tool_executed",
            tool=tool_name,
            found=result.get("found", False),
            source_count=len(result.get("sources", [])),
            latency_ms=latency_ms,
        )
        return {
            "success": True,
            "found": result.get("found", False),
            "sources": result.get("sources", []),
            "error_code": result.get("error"),
        }
    except Exception as exc:
        latency_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("tool_execution_failed", tool=tool_name, error=str(exc), latency_ms=latency_ms)
        return {
            "success": False,
            "found": False,
            "sources": [],
            "error_code": "KNOWLEDGE_RETRIEVAL_FAILED",
        }
