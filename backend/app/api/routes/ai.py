from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.ai import ChatConversation, ChatMessage
from app.models.user import User
from app.schemas.ai import (ChatMessageIn, ChatMessageOut, StoredChatMessageOut, SummaryOut)
from app.services.ai_service import build_grounded_answer, maybe_ai_polish, pick_application, visible_application

router = APIRouter(tags=["AI Assistant"])


def _base_route(user: User) -> str:
    return {"INSTITUTION": "/institution", "OFFICER": "/officer", "ADMIN": "/admin"}.get(user.role, "/institution")


@router.post("/chat/messages", response_model=ChatMessageOut)
def chat(payload: ChatMessageIn, user: User = Depends(get_current_user),
         db: Session = Depends(get_db)) -> ChatMessageOut:
    application = pick_application(db, user, payload.application_id)
    if payload.application_id is not None and application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    if payload.conversation_id is not None:
        conversation = db.get(ChatConversation, payload.conversation_id)
        if conversation is None or conversation.user_id != user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = ChatConversation(user_id=user.id, application_id=application.id if application else None)
        db.add(conversation)
        db.flush()

    db.add(ChatMessage(conversation_id=conversation.id, role="user", content=payload.message))

    answer, sources, actions, needs_human = build_grounded_answer(db, user, payload.message, application)
    context = [f"Q: {payload.message}", f"A: {answer}"]
    polished = maybe_ai_polish(payload.message, answer, context)
    final_answer = polished or answer
    used_ai = polished is not None

    db.add(ChatMessage(conversation_id=conversation.id, role="assistant", content=final_answer, sources=sources))
    db.commit()
    return ChatMessageOut(conversation_id=conversation.id, answer=final_answer, sources=sources,
                          suggested_actions=actions, used_ai=used_ai, needs_human_review=needs_human)


@router.get("/chat/conversations/{conversation_id}/messages", response_model=list[StoredChatMessageOut])
def conversation_messages(conversation_id: int, user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)) -> list[StoredChatMessageOut]:
    conversation = db.get(ChatConversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.scalars(select(ChatMessage).where(ChatMessage.conversation_id == conversation.id)
                          .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())).all()
    return [StoredChatMessageOut.model_validate(item) for item in messages]


@router.get("/applications/{application_id}/summary", response_model=SummaryOut)
def summary(application_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> SummaryOut:
    application = visible_application(db, user, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    from app.services.ai_service import latest_results
    from app.services.workflow_service import ALLOWED_TRANSITIONS
    from app.models.query import Query

    results = latest_results(db, application.id)
    failed = [r for r in results if r.status == "FAIL"]
    open_queries = db.scalars(select(Query).where(Query.application_id == application.id, Query.status == "OPEN")).all()
    parts = [f"{application.application_code}: {application.title}. Current stage: {application.current_stage}."]
    if application.due_at is not None:
        parts.append(f"Deadline: {application.due_at.isoformat()}.")
    if results:
        parts.append("Compliance (latest): "
                     + "; ".join(f"{r.rule_code} {r.status}" for r in results) + ".")
    if open_queries:
        parts.append(f"Open query(s): {len(open_queries)}.")
    allowed = sorted(ALLOWED_TRANSITIONS.get(application.current_stage, set()))
    if user.role in ("OFFICER", "ADMIN") and allowed:
        next_action = f"Permitted stage action(s): {', '.join(allowed)}."
    elif open_queries:
        next_action = "Wait for the institution to respond to open query(s), then continue review."
    elif failed:
        next_action = "Request corrected evidence/data, then re-run the compliance check."
    else:
        next_action = "Continue the review per the workflow stage."
    summary_text = " ".join(parts)
    polished = maybe_ai_polish("Summarize this case", summary_text, [summary_text])
    return SummaryOut(application_id=application.id, summary=polished or summary_text,
                      next_action=next_action, generated_by="ai" if polished else "deterministic")
