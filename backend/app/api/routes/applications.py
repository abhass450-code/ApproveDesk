from datetime import datetime, timezone
from pathlib import Path
from secrets import token_hex
from fastapi import APIRouter, Depends, File, HTTPException, Query as QueryParam, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models.application import Application
from app.models.application_stage import ApplicationStage
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.query import Query
from app.models.user import User
from app.schemas.application import (ApplicationCreate, ApplicationOut, ApplicationHistoryOut,
                                     AssignmentRequest, AuditLogOut, StageHistoryOut, TransitionRequest)
from app.schemas.common import ApplicationStatus, UserRole
from app.schemas.query import QueryCreate, QueryOut
from app.services.audit_service import append_audit
from app.services.workflow_service import transition_application

router = APIRouter(prefix="/applications", tags=["Applications"])
settings = get_settings()
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _visible_application(db: Session, application_id: int, user: User) -> Application:
    app = db.get(Application, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if user.role == UserRole.ADMIN.value:
        return app
    if user.role == UserRole.INSTITUTION.value and app.institution_id == user.institution_id:
        return app
    if user.role == UserRole.OFFICER.value and app.assigned_officer_id == user.id:
        return app
    # Return 404 so callers cannot use the API to discover another tenant's IDs.
    raise HTTPException(status_code=404, detail="Application not found")


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate,
                       user: User = Depends(require_roles(UserRole.INSTITUTION)),
                       db: Session = Depends(get_db)) -> ApplicationOut:
    if user.institution_id is None:
        raise HTTPException(status_code=403, detail="Institution user is not linked to an institution")
    code = f"APP-{datetime.now(timezone.utc):%Y%m%d}-{token_hex(3).upper()}"
    application = Application(application_code=code, institution_id=user.institution_id,
                              created_by_id=user.id, title=payload.title.strip(), description=payload.description,
                              current_stage=ApplicationStatus.SUBMITTED.value)
    db.add(application)
    db.flush()
    db.add(ApplicationStage(application_id=application.id, from_stage=None,
                            to_stage=ApplicationStatus.SUBMITTED.value, changed_by_id=user.id,
                            note="Application submitted"))
    append_audit(db, actor_id=user.id, action="APPLICATION_SUBMITTED", entity_type="application",
                 entity_id=application.id, details={"application_code": code})
    db.commit()
    db.refresh(application)
    return ApplicationOut.model_validate(application)


@router.get("", response_model=list[ApplicationOut])
def list_applications(skip: int = QueryParam(default=0, ge=0), limit: int = QueryParam(default=50, ge=1, le=100),
                      current_status: ApplicationStatus | None = QueryParam(default=None, alias="status"),
                      user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ApplicationOut]:
    stmt = select(Application)
    if user.role == UserRole.INSTITUTION.value:
        stmt = stmt.where(Application.institution_id == user.institution_id)
    elif user.role == UserRole.OFFICER.value:
        stmt = stmt.where(Application.assigned_officer_id == user.id)
    elif user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Insufficient role")
    if current_status is not None:
        stmt = stmt.where(Application.current_stage == current_status.value)
    apps = db.scalars(stmt.order_by(Application.created_at.desc()).offset(skip).limit(limit)).all()
    return [ApplicationOut.model_validate(app) for app in apps]


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(application_id: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)) -> ApplicationOut:
    return ApplicationOut.model_validate(_visible_application(db, application_id, user))


@router.post("/{application_id}/transition", response_model=ApplicationOut)
def transition(application_id: int, payload: TransitionRequest,
               user: User = Depends(require_roles(UserRole.OFFICER, UserRole.ADMIN)),
               db: Session = Depends(get_db)) -> ApplicationOut:
    application = _visible_application(db, application_id, user)
    transition_application(db, application, user, payload.to_stage, payload.note)
    db.commit()
    db.refresh(application)
    return ApplicationOut.model_validate(application)


@router.patch("/{application_id}/assignment", response_model=ApplicationOut)
def assign_officer(application_id: int, payload: AssignmentRequest,
                   user: User = Depends(require_roles(UserRole.ADMIN)),
                   db: Session = Depends(get_db)) -> ApplicationOut:
    application = _visible_application(db, application_id, user)
    officer = db.get(User, payload.assigned_officer_id)
    if officer is None or not officer.is_active or officer.role != UserRole.OFFICER.value:
        raise HTTPException(status_code=422, detail="assigned_officer_id must reference an active OFFICER")
    previous_officer_id = application.assigned_officer_id
    application.assigned_officer_id = officer.id
    db.add(application)
    append_audit(db, actor_id=user.id, action="APPLICATION_ASSIGNED", entity_type="application",
                 entity_id=application.id, details={"previous_officer_id": previous_officer_id,
                                                    "assigned_officer_id": officer.id})
    db.commit()
    db.refresh(application)
    return ApplicationOut.model_validate(application)


@router.get("/{application_id}/history", response_model=ApplicationHistoryOut)
def application_history(application_id: int, user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)) -> ApplicationHistoryOut:
    application = _visible_application(db, application_id, user)
    stages = db.scalars(select(ApplicationStage).where(ApplicationStage.application_id == application.id)
                        .order_by(ApplicationStage.created_at.asc(), ApplicationStage.id.asc())).all()
    audit_events = db.scalars(select(AuditLog).where(AuditLog.entity_type == "application",
                                                       AuditLog.entity_id == application.id)
                              .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())).all()
    return ApplicationHistoryOut(application_id=application.id,
                                 stages=[StageHistoryOut.model_validate(item) for item in stages],
                                 audit_events=[AuditLogOut.model_validate(item) for item in audit_events])


@router.get("/{application_id}/queries", response_model=list[QueryOut])
def list_application_queries(application_id: int, user: User = Depends(get_current_user),
                             db: Session = Depends(get_db)) -> list[QueryOut]:
    application = _visible_application(db, application_id, user)
    items = db.scalars(select(Query).where(Query.application_id == application.id)
                       .order_by(Query.created_at.asc(), Query.id.asc())).all()
    return [QueryOut.model_validate(item) for item in items]


@router.post("/{application_id}/queries", response_model=QueryOut, status_code=status.HTTP_201_CREATED)
def create_query(application_id: int, payload: QueryCreate, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)) -> QueryOut:
    application = _visible_application(db, application_id, user)
    query = Query(application_id=application.id, raised_by_id=user.id, message=payload.message.strip(),
                  due_at=payload.due_at, status="OPEN")
    db.add(query)
    db.flush()
    append_audit(db, actor_id=user.id, action="QUERY_RAISED", entity_type="query", entity_id=query.id,
                 details={"application_id": application.id})
    db.commit()
    db.refresh(query)
    return QueryOut.model_validate(query)


@router.post("/{application_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(application_id: int, file: UploadFile = File(...),
                          user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    application = _visible_application(db, application_id, user)
    original_name = Path(file.filename or "document.bin").name[:255]
    suffix = Path(original_name).suffix[:16]
    stored_name = f"{token_hex(16)}{suffix}"
    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if not contents:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MiB demo upload limit")
    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = upload_dir / stored_name
    target.write_bytes(contents)
    document = Document(application_id=application.id, filename=original_name,
                        content_type=file.content_type, storage_path=str(target), uploaded_by_id=user.id)
    db.add(document)
    db.flush()
    append_audit(db, actor_id=user.id, action="DOCUMENT_UPLOADED", entity_type="document", entity_id=document.id,
                 details={"application_id": application.id, "filename": original_name})
    db.commit()
    return {"id": document.id, "application_id": document.application_id, "filename": document.filename,
            "content_type": document.content_type, "verified": document.verified, "created_at": document.created_at}
