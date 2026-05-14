import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User, Conversation, Message, GuardrailPolicy
from auth.middleware import get_current_user
from auth.service import AuthService
from agents.orchestrator import Orchestrator
from guardrails.checker import GuardrailChecker

logger = logging.getLogger("soc.chat")

router = APIRouter()
orchestrator = Orchestrator()

GUARDRAIL_REFUSAL = (
    "I can't help with that request. This assistant only handles defensive "
    "security operations (network, identity, and policy). If you have a legitimate "
    "SOC question, please rephrase it without instructions to override safety rules."
)


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    response: str
    agent: str
    conversation_id: int
    blocked: bool = False
    severity: str | None = None


def _load_extra_patterns(db: Session) -> list[str]:
    return [
        row.pattern
        for row in db.query(GuardrailPolicy).filter(GuardrailPolicy.is_active.is_(True)).all()
    ]


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Get or create conversation up front so blocked attempts still get logged.
    if body.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == body.conversation_id,
            Conversation.user_id == user.id,
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(user_id=user.id, title=body.message[:80])
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        AuthService.log_security_event(
            db,
            event_type="conversation_created",
            status="success",
            email=user.email,
            user_id=user.id,
            ip_address=_ip(request),
            details=f"conversation_id={conversation.id}",
        )

    # Guardrail check on input -> safe refusal returned as a normal assistant message.
    extra_patterns = _load_extra_patterns(db)
    input_check = GuardrailChecker.check_input(body.message, extra_patterns=extra_patterns)
    if not input_check["safe"]:
        logger.warning(
            "GUARDRAIL_BLOCK user_id=%s reason=%r message_preview=%r",
            user.id, input_check["reason"], body.message[:120],
        )
        AuthService.log_security_event(
            db,
            event_type="guardrail_block",
            status="blocked",
            email=user.email,
            user_id=user.id,
            ip_address=_ip(request),
            details=f"reason={input_check['reason']} matched={input_check.get('matched_pattern','')}",
        )
        db.add(Message(conversation_id=conversation.id, role="user", content=body.message))
        db.add(Message(
            conversation_id=conversation.id,
            role="assistant",
            content=GUARDRAIL_REFUSAL,
            agent_used="guardrail",
        ))
        db.commit()
        return ChatResponse(
            response=GUARDRAIL_REFUSAL,
            agent="guardrail",
            conversation_id=conversation.id,
            blocked=True,
        )

    # Build conversation history
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in conversation.messages
        if msg.role in ("user", "assistant")
    ]

    # Route to agent
    result = await orchestrator.handle(body.message, history)

    # Audit the routing decision
    AuthService.log_security_event(
        db,
        event_type="routing_decision",
        status="success",
        email=user.email,
        user_id=user.id,
        ip_address=_ip(request),
        details=(
            f"agent={result['agent']} severity={result['severity']} "
            f"conversation_id={conversation.id}"
        ),
    )

    # Guardrail check on output
    output_check = GuardrailChecker.check_output(result["response"])
    if not output_check["safe"]:
        logger.warning(
            "GUARDRAIL_OUTPUT_BLOCK user_id=%s reason=%r",
            user.id, output_check["reason"],
        )
        AuthService.log_security_event(
            db,
            event_type="guardrail_block",
            status="blocked",
            email=user.email,
            user_id=user.id,
            ip_address=_ip(request),
            details=f"output_block reason={output_check['reason']}",
        )
        result["response"] = (
            "I cannot share that response as it may contain sensitive information."
        )

    # Save messages
    db.add(Message(conversation_id=conversation.id, role="user", content=body.message))
    db.add(Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["response"],
        agent_used=result["agent"],
        severity=result["severity"],
    ))
    AuthService.log_security_event(
        db,
        event_type="chat_message",
        status="success",
        email=user.email,
        user_id=user.id,
        ip_address=_ip(request),
        details=f"agent={result['agent']} conversation_id={conversation.id}",
    )
    db.commit()

    return ChatResponse(
        response=result["response"],
        agent=result["agent"],
        conversation_id=conversation.id,
        severity=result["severity"],
    )
