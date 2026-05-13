import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User, Conversation, Message
from auth.middleware import get_current_user
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


@router.post("/", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
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

    # Guardrail check on input -> return safe refusal as a normal assistant message.
    input_check = GuardrailChecker.check_input(body.message)
    if not input_check["safe"]:
        logger.warning(
            "GUARDRAIL_BLOCK user_id=%s reason=%r message_preview=%r",
            user.id, input_check["reason"], body.message[:120],
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

    # Guardrail check on output
    output_check = GuardrailChecker.check_output(result["response"])
    if not output_check["safe"]:
        logger.warning(
            "GUARDRAIL_OUTPUT_BLOCK user_id=%s reason=%r",
            user.id, output_check["reason"],
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
    ))
    db.commit()

    return ChatResponse(
        response=result["response"],
        agent=result["agent"],
        conversation_id=conversation.id,
    )
