from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User, Conversation, Message
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
