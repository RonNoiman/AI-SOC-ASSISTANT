import re

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User, Conversation, Message, SecurityEvent, GuardrailPolicy
from auth.middleware import require_admin
from auth.service import AuthService

router = APIRouter()


class StatsResponse(BaseModel):
    total_users: int
    total_conversations: int
    total_messages: int
    total_security_events: int
    locked_users: int


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    is_active: bool
    failed_login_attempts: int
    is_locked: bool

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
    acknowledged: bool = False


class GuardrailPolicyOut(BaseModel):
    id: int
    pattern: str
    reason: str
    is_active: bool
    created_at: str
    acknowledged: bool = False


class GuardrailPolicyCreate(BaseModel):
    pattern: str
    reason: str = "Custom admin policy"

class RoleUpdate(BaseModel):
    role: str

class StatusUpdate(BaseModel):
    is_active: bool


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    locked = db.query(User).filter(User.locked_until.isnot(None)).all()
    locked_count = sum(1 for u in locked if AuthService.is_user_locked(u))
    return StatsResponse(
        total_users=db.query(User).count(),
        total_conversations=db.query(Conversation).count(),
        total_messages=db.query(Message).count(),
        total_security_events=db.query(SecurityEvent).count(),
        locked_users=locked_count,
    )


@router.get("/users", response_model=list[UserOut])
async def list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id).all()
    return [
        UserOut(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            failed_login_attempts=u.failed_login_attempts or 0,
            is_locked=AuthService.is_user_locked(u),
        )
        for u in users
    ]


@router.post("/users/{user_id}/unlock")
async def unlock_user(
    user_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    was_locked = AuthService.is_user_locked(user)
    AuthService.reset_login_attempts(db, user)
    AuthService.log_security_event(
        db,
        event_type="account_unlock",
        status="success",
        email=user.email,
        user_id=user.id,
        ip_address=_ip(request),
        details=f"unlocked_by_admin={admin.email} was_locked={was_locked}",
    )
    return {"detail": f"User {user.email} unlocked.", "was_locked": was_locked}

@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    body: RoleUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if body.role not in ("admin", "analyst"):
        raise HTTPException(status_code=400, detail="Invalid role")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = user.role
    user.role = body.role
    db.commit()
    AuthService.log_security_event(
        db, event_type="user_modified", status="success", email=user.email, user_id=user.id,
        ip_address=_ip(request), details=f"role changed from {old_role} to {body.role} by {admin.email}"
    )
    return {"detail": "Role updated"}

@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    body: StatusUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
        
    user.is_active = body.is_active
    db.commit()
    AuthService.log_security_event(
        db, event_type="user_modified", status="success", email=user.email, user_id=user.id,
        ip_address=_ip(request), details=f"is_active changed to {body.is_active} by {admin.email}"
    )
    return {"detail": "Status updated"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from database.models import PasswordResetToken
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
    email = user.email
    
    # Manually delete conversations to trigger ORM cascades for messages
    conversations = db.query(Conversation).filter(Conversation.user_id == user.id).all()
    for c in conversations:
        db.delete(c)
        
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete()
    db.query(SecurityEvent).filter(SecurityEvent.user_id == user.id).update({"user_id": None})
    db.query(GuardrailPolicy).filter(GuardrailPolicy.created_by == user.id).update({"created_by": None})
    
    db.delete(user)
    db.commit()
    
    AuthService.log_security_event(
        db, event_type="user_deleted", status="success", email=email,
        ip_address=_ip(request), details=f"deleted by {admin.email}"
    )
    return {"detail": "User deleted"}


@router.get("/security-events", response_model=list[SecurityEventOut])
async def list_security_events(
    event_type: str | None = None,
    limit: int = 100,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(SecurityEvent).order_by(SecurityEvent.created_at.desc())
    if event_type:
        q = q.filter(SecurityEvent.event_type == event_type)
    events = q.limit(min(limit, 500)).all()
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
            acknowledged=bool(event.acknowledged),
        )
        for event in events
    ]


@router.get("/guardrail-policies", response_model=list[GuardrailPolicyOut])
async def list_policies(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(GuardrailPolicy).order_by(GuardrailPolicy.created_at.desc()).all()
    return [
        GuardrailPolicyOut(
            id=p.id,
            pattern=p.pattern,
            reason=p.reason,
            is_active=p.is_active,
            created_at=str(p.created_at),
        )
        for p in rows
    ]


@router.post("/guardrail-policies", response_model=GuardrailPolicyOut)
async def create_policy(
    body: GuardrailPolicyCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        re.compile(body.pattern)
    except re.error as exc:
        raise HTTPException(status_code=400, detail=f"Invalid regex: {exc}")

    policy = GuardrailPolicy(
        pattern=body.pattern,
        reason=body.reason or "Custom admin policy",
        is_active=True,
        created_by=admin.id,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    AuthService.log_security_event(
        db,
        event_type="guardrail_policy_change",
        status="created",
        email=admin.email,
        user_id=admin.id,
        ip_address=_ip(request),
        details=f"policy_id={policy.id} pattern={policy.pattern}",
    )
    return GuardrailPolicyOut(
        id=policy.id,
        pattern=policy.pattern,
        reason=policy.reason,
        is_active=policy.is_active,
        created_at=str(policy.created_at),
    )


@router.delete("/guardrail-policies/{policy_id}")
async def delete_policy(
    policy_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    policy = db.query(GuardrailPolicy).filter(GuardrailPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    pattern = policy.pattern
    db.delete(policy)
    db.commit()
    AuthService.log_security_event(
        db,
        event_type="guardrail_policy_change",
        status="deleted",
        email=admin.email,
        user_id=admin.id,
        ip_address=_ip(request),
        details=f"policy_id={policy_id} pattern={pattern}",
    )
    return {"detail": "Policy deleted."}


@router.post("/security-events/acknowledge-all")
async def acknowledge_all_events(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    unacknowledged = db.query(SecurityEvent).filter(
        SecurityEvent.event_type == "guardrail_block",
        SecurityEvent.acknowledged == False
    ).all()
    
    count = len(unacknowledged)
    for event in unacknowledged:
        event.acknowledged = True
        
    db.commit()
    return {"detail": f"{count} alerts acknowledged."}

@router.post("/security-events/{event_id}/acknowledge")
async def acknowledge_event(
    event_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.acknowledged = True
    db.commit()
    return {"detail": "Alert acknowledged."}
