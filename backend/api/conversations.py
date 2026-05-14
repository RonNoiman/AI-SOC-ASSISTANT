from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User, Conversation, Message
from auth.middleware import get_current_user

router = APIRouter()

# Highest to lowest, so a conversation's "top" risk is its worst message.
SEVERITY_RANK = {"Critical": 5, "High": 4, "Medium": 3, "Low": 2, "Informational": 1}


class ConversationSummary(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str
    message_count: int
    agents: list[str]          # distinct assistant agents that replied in this conversation
    top_severity: str | None   # worst triage severity across the conversation's messages

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    agent_used: str | None
    severity: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=list[ConversationSummary])
async def list_conversations(
    q: str | None = None,
    agent: str | None = None,
    severity: str | None = None,
    sort: str = "newest",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the analyst's conversations with optional search/filter/sort.

    - ``q``: matches the title or any message content.
    - ``agent``: keep conversations that include a reply from this agent.
    - ``severity``: keep conversations with a reply at this risk level.
    - ``sort``: ``newest`` (default) or ``oldest`` by last activity.
    """
    query = db.query(Conversation).filter(Conversation.user_id == user.id)

    if q and q.strip():
        like = f"%{q.strip()}%"
        # Match conversations whose title matches OR which contain any message matching.
        matching_conv_ids = (
            db.query(Message.conversation_id)
            .filter(Message.content.ilike(like))
            .distinct()
        )
        query = query.filter(
            or_(
                Conversation.title.ilike(like),
                Conversation.id.in_(matching_conv_ids),
            )
        )

    if agent:
        agent_conv_ids = (
            db.query(Message.conversation_id)
            .filter(Message.agent_used == agent)
            .distinct()
        )
        query = query.filter(Conversation.id.in_(agent_conv_ids))

    if severity:
        severity_conv_ids = (
            db.query(Message.conversation_id)
            .filter(Message.severity == severity)
            .distinct()
        )
        query = query.filter(Conversation.id.in_(severity_conv_ids))

    order = (
        Conversation.updated_at.asc()
        if sort == "oldest"
        else Conversation.updated_at.desc()
    )
    conversations = query.order_by(order).all()

    summaries = []
    for c in conversations:
        agents_used = sorted({m.agent_used for m in c.messages if m.agent_used})
        severities = [m.severity for m in c.messages if m.severity]
        top_severity = (
            max(severities, key=lambda s: SEVERITY_RANK.get(s, 0))
            if severities
            else None
        )
        summaries.append(
            ConversationSummary(
                id=c.id,
                title=c.title,
                created_at=str(c.created_at),
                updated_at=str(c.updated_at),
                message_count=len(c.messages),
                agents=agents_used,
                top_severity=top_severity,
            )
        )
    return summaries


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return [
        MessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            agent_used=m.agent_used,
            severity=m.severity,
            created_at=str(m.created_at),
        )
        for m in conversation.messages
    ]


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conversation)
    db.commit()
    return {"detail": "Conversation deleted"}
