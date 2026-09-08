"""
RAG service — real retrieval-augmented generation using pgvector.

Pipeline:
  Customer question
    → embed with OpenAI text-embedding-3-small
    → cosine similarity search against knowledge_documents
    → score >= threshold → return context
    → score < threshold → found=False (LLM must NOT fabricate)
"""
from typing import Optional
import openai
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.config.logging import logger
from app.db.models import KnowledgeDocument


_client: Optional[openai.AsyncOpenAI] = None


def _get_openai_client() -> openai.AsyncOpenAI:
    global _client
    if _client is None:
        _client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def embed_text(text_input: str) -> list[float]:
    """Generate an embedding for a text string using OpenAI."""
    client = _get_openai_client()
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text_input,
    )
    return response.data[0].embedding


async def embed_all_documents(db: AsyncSession, restaurant_id: int) -> int:
    """
    Embed all knowledge documents that don't have embeddings yet.
    Called once after seeding or when new documents are added.
    Returns count of documents embedded.
    """
    result = await db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.restaurant_id == restaurant_id,
            KnowledgeDocument.embedding == None,  # noqa: E711
        )
    )
    docs = result.scalars().all()

    count = 0
    for doc in docs:
        try:
            embedding = await embed_text(doc.content)
            doc.embedding = embedding
            count += 1
            logger.info("document_embedded", doc_id=doc.id, title=doc.title)
        except Exception as exc:
            logger.error("embed_failed", doc_id=doc.id, error=str(exc))

    if count > 0:
        await db.commit()

    return count


async def search_knowledge(
    db: AsyncSession,
    restaurant_id: int,
    query: str,
) -> dict:
    """
    Semantic search over knowledge_documents using pgvector cosine similarity.

    Returns:
        { found: True, sources: [...] }  — with context for the LLM
        { found: False, sources: [] }    — LLM MUST NOT fabricate an answer

    This is the anti-hallucination gate for natural-language restaurant questions.
    """
    if not settings.openai_api_key:
        return {
            "found": False,
            "sources": [],
            "error": "embedding_service_unavailable",
        }

    try:
        query_embedding = await embed_text(query)
    except Exception as exc:
        logger.error("rag_embed_failed", error=str(exc))
        return {"found": False, "sources": [], "error": "embedding_failed"}

    try:
        # pgvector cosine distance: 1 - cosine_similarity
        # Lower distance = more similar
        sql = text("""
            SELECT
                id,
                title,
                content,
                1 - (embedding <=> CAST(:embedding AS vector)) AS score
            FROM knowledge_documents
            WHERE restaurant_id = :restaurant_id
              AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """)

        result = await db.execute(
            sql,
            {
                "embedding": str(query_embedding),
                "restaurant_id": restaurant_id,
                "top_k": settings.rag_top_k,
            },
        )
        rows = result.fetchall()

        sources = []
        for row in rows:
            score = float(row.score)
            if score >= settings.rag_similarity_threshold:
                sources.append({
                    "id": row.id,
                    "title": row.title,
                    "content": row.content,
                    "score": round(score, 4),
                })

        found = len(sources) > 0

        logger.info(
            "rag_search",
            query=query[:60],
            results=len(rows),
            above_threshold=len(sources),
            found=found,
        )

        return {"found": found, "sources": sources}

    except Exception as exc:
        logger.error("rag_search_failed", error=str(exc))
        return {"found": False, "sources": [], "error": "retrieval_failed"}
