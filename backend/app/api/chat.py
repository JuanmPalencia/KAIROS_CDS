"""
Internal operator chat — lightweight in-memory message store.
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/api/chat", tags=["chat"])

# ── In-memory store (replace with DB/Redis for production) ──
_messages: List[dict] = []
MAX_MESSAGES = 500


class ChatMessageIn(BaseModel):
    text: str
    channel: str = "general"  # general | dispatch | medical


class ChatMessageOut(BaseModel):
    id: str
    user: str
    role: str
    text: str
    channel: str
    ts: str  # ISO timestamp


@router.get("/messages", response_model=List[ChatMessageOut])
def get_messages(
    channel: str = Query("general"),
    since: Optional[str] = Query(None, description="ISO timestamp to get messages after"),
    current_user=Depends(get_current_user),
):
    """Return recent messages for a channel, optionally filtered by timestamp."""
    msgs = [m for m in _messages if m["channel"] == channel]
    if since:
        msgs = [m for m in msgs if m["ts"] > since]
    return msgs[-100:]  # last 100


@router.post("/messages", response_model=ChatMessageOut)
def post_message(
    body: ChatMessageIn,
    current_user=Depends(get_current_user),
):
    """Send a message to a channel."""
    global _messages
    msg = {
        "id": str(uuid4()),
        "user": current_user.username if hasattr(current_user, 'username') else current_user.get("sub", "unknown"),
        "role": current_user.role if hasattr(current_user, 'role') else current_user.get("role", "OPERATOR"),
        "text": body.text.strip()[:500],
        "channel": body.channel,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    _messages.append(msg)
    # Trim old messages
    if len(_messages) > MAX_MESSAGES:
        _messages = _messages[-MAX_MESSAGES:]
    return msg


@router.get("/channels")
def get_channels(current_user=Depends(get_current_user)):
    """Available chat channels."""
    return [
        {"id": "general", "name": "General", "icon": "💬"},
        {"id": "dispatch", "name": "Despacho", "icon": "🚑"},
        {"id": "medical", "name": "Médico", "icon": "🏥"},
    ]
