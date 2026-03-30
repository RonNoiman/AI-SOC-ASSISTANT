from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User, Conversation, Message
from auth.middleware import get_current_user
from agents.orchestrator import Orchestrator
from guardrails.checker import GuardrailChecker

router = APIRouter()
orchestrator = Orchestrator()


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    response: str
    agent: str
    conversation_id: int


@router.post("/", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Guardrail check on input
    input_check = GuardrailChecker.check_input(body.message)
    if not input_check["safe"]:
        raise HTTPException(status_code=400, detail=input_check["reason"])

    # Get or create conversation
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

    # Build conversation history
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in conversation.messages
    ]

    # Route to agent
    result = await orchestrator.handle(body.message, history)

    # Guardrail check on output
    output_check = GuardrailChecker.check_output(result["response"])
    if not output_check["safe"]:
        result["response"] = "I cannot provide that response as it may contain sensitive information."

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
