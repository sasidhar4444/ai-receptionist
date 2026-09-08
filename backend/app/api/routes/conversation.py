"""Conversation session and text messaging routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import ConversationSession
from app.config.settings import settings
from app.config.logging import logger
from app.agents.receptionist_agent import receptionist_agent
from app.agents.schemas import TextMessageRequest, TextMessageResponse

router = APIRouter(prefix="/conversation", tags=["conversation"])

# In-memory history cache for prototype session tracking
_session_history: dict[str, list[dict]] = {}


@router.post("/session")
async def create_session(db: AsyncSession = Depends(get_db)):
    """
    Create a new conversation session.
    Persists session in PostgreSQL and initializes session history.
    """
    session_id = f"sess_{uuid.uuid4().hex[:12]}"

    new_session = ConversationSession(
        session_id=session_id,
        restaurant_id=settings.restaurant_id,
        state="idle",
    )
    db.add(new_session)
    await db.commit()

    _session_history[session_id] = []
    logger.info("session_created", session_id=session_id)

    return {"session_id": session_id, "state": "idle"}


@router.post("/message", response_model=TextMessageResponse)
async def send_message(
    payload: TextMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Text fallback message endpoint.
    Runs through the EXACT same LLM + Tool calling pipeline as voice.
    Customer input → ReceptionistAgent (GPT-4o + tools) → Database tools → Spoken/Text response.
    """
    session_id = payload.session_id
    text = payload.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    history = _session_history.get(session_id, [])

    # Process turn with receptionist agent
    response = await receptionist_agent.chat(
        session_id=session_id,
        user_message=text,
        history=history,
        db=db,
        restaurant_id=settings.restaurant_id,
    )

    # Update conversation history
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": response.response})
    _session_history[session_id] = history[-20:]  # keep last 20 messages

    return response


@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve session details and recent messages."""
    result = await db.execute(
        select(ConversationSession).where(ConversationSession.session_id == session_id)
    )
    sess = result.scalars().first()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": sess.session_id,
        "state": sess.state,
        "created_at": sess.created_at.isoformat() if sess.created_at else None,
        "history": _session_history.get(session_id, []),
    }
