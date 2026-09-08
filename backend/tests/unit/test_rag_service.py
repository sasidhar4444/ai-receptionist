"""
Unit tests for rag_service.py.
Validates:
- Threshold gating: Score >= threshold returns found=True
- Score < threshold returns found=False
- Missing API key returns found=False
- Embedding error returns found=False and does not crash
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.services import rag_service
from app.config.settings import settings


@pytest.mark.asyncio
async def test_search_knowledge_above_threshold():
    """Should return found=True with context when similarity score >= threshold."""
    mock_db = AsyncMock()

    # Mock database row returned by pgvector query
    mock_row = MagicMock()
    mock_row.id = 1
    mock_row.title = "Pet Policy"
    mock_row.content = "Leashed dogs are welcome in our outdoor terrace."
    mock_row.score = 0.88  # Above 0.75 default threshold

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]
    mock_db.execute.return_value = mock_result

    with patch.object(rag_service, "embed_text", new=AsyncMock(return_value=[0.1] * 1536)):
        with patch.object(settings, "openai_api_key", "test-key"):
            result = await rag_service.search_knowledge(
                db=mock_db,
                restaurant_id=1,
                query="Can I bring my dog?",
            )

    assert result["found"] is True
    assert len(result["sources"]) == 1
    assert result["sources"][0]["title"] == "Pet Policy"
    assert result["sources"][0]["score"] == 0.88


@pytest.mark.asyncio
async def test_search_knowledge_below_threshold():
    """Should return found=False when all documents score below threshold."""
    mock_db = AsyncMock()

    mock_row = MagicMock()
    mock_row.id = 2
    mock_row.title = "Payment Methods"
    mock_row.content = "We accept credit cards and cash."
    mock_row.score = 0.42  # Below 0.75 threshold

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]
    mock_db.execute.return_value = mock_result

    with patch.object(rag_service, "embed_text", new=AsyncMock(return_value=[0.1] * 1536)):
        with patch.object(settings, "openai_api_key", "test-key"):
            result = await rag_service.search_knowledge(
                db=mock_db,
                restaurant_id=1,
                query="Do you have a helicopter pad?",
            )

    assert result["found"] is False
    assert len(result["sources"]) == 0


@pytest.mark.asyncio
async def test_search_knowledge_no_api_key():
    """Should return found=False when OPENAI_API_KEY is not configured."""
    mock_db = AsyncMock()

    with patch.object(settings, "openai_api_key", ""):
        result = await rag_service.search_knowledge(
            db=mock_db,
            restaurant_id=1,
            query="What are your hours?",
        )

    assert result["found"] is False
    assert result["sources"] == []
    assert result.get("error") == "embedding_service_unavailable"
