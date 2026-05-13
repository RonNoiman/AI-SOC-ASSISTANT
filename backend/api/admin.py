from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User, Conversation, Message, SecurityEvent
from auth.middleware import require_admin

router = APIRouter()


class StatsResponse(BaseModel):
    total_users: int
    total_conversations: int
    total_messages: int


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class SecurityEventOut(BaseModel):
    id: int
    event_type: str
    email: str | None
    user_id: int | None
    status: str
    ip_address: str | None
    details: str | None
    created_at: str


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return StatsResponse(
        total_users=db.query(User).count(),
        total_conversations=db.query(Conversation).count(),
        total_messages=db.query(Message).count(),
    )


@router.get("/users", response_model=list[UserOut])
async def list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).all()


@router.get("/security-events", response_model=list[SecurityEventOut])
async def list_security_events(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    events = (
        db.query(SecurityEvent)
        .order_by(SecurityEvent.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        SecurityEventOut(
            id=event.id,
            event_type=event.event_type,
            email=event.email,
            user_id=event.user_id,
            status=event.status,
            ip_address=event.ip_address,
            details=event.details,
            created_at=str(event.created_at),
        )
        for event in events
    ]
