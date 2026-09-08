"""Pydantic schemas for tool inputs, outputs, and conversation messages."""
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ─── Tool Inputs ──────────────────────────────────────────────────────────
class FindAvailableTableInput(BaseModel):
    party_size: int = Field(..., ge=1, le=20, description="Number of guests")
    zone: Optional[str] = Field(None, description="Preferred zone: indoor, outdoor, private, or any")


class GetRestaurantInfoInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Customer's question")


class GetLiveTableStateInput(BaseModel):
    pass  # No input needed — returns all tables


# ─── Tool Outputs ─────────────────────────────────────────────────────────
class ToolResult(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[dict] = None
    source: str = "unknown"


# ─── Conversation ─────────────────────────────────────────────────────────
class ConversationMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class TextMessageRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1, max_length=2000)


class TextMessageResponse(BaseModel):
    session_id: str
    response: str
    state: str = "idle"
