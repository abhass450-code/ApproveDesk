from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.application import Application
from app.models.query import Query, QueryResponse
from app.models.user import User
from app.schemas.common import UserRole
from app.schemas.query import QueryResponseCreate, QueryResponseOut
from app.services.audit_service import append_audit

router = APIRouter(prefix="/queries", tags=["Queries"])


def _can_access(application: Application, user: User) -> bool:
    if user.role == UserRole.ADMIN.value:
        return True
    if user.role == UserRole.INSTITUTION.value:
        return application.institution_id == user.institution_id
    if user.role == UserRole.OFFICER.value:
        return application.assigned_officer_id == user.id
    return False


@router.post("/{query_id}/responses", response_model=QueryResponseOut, status_code=201)
def respond(query_id: int, payload: QueryResponseCreate, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)) -> QueryResponseOut:
    query = db.get(Query, query_id)
    if query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    application = db.get(Application, query.application_id)
    if application is None or not _can_access(application, user):
        raise HTTPException(status_code=404, detail="Query not found")
    if query.status == "CLOSED":
        raise HTTPException(status_code=422, detail="Closed queries cannot receive responses")
    response = QueryResponse(query_id=query.id, responder_id=user.id, message=payload.message.strip())
    db.add(response)
    query.status = "RESPONDED"
    append_audit(db, actor_id=user.id, action="QUERY_RESPONSE_ADDED", entity_type="query", entity_id=query.id,
                 details={"application_id": application.id})
    db.commit()
    db.refresh(response)
    return QueryResponseOut.model_validate(response)
