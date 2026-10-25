from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.application import Application
from app.models.application_stage import ApplicationStage
from app.models.user import User
from app.schemas.common import ApplicationStatus, UserRole
from app.services.audit_service import append_audit


# Normal transitions are deliberately explicit. CORRECTION_REQUIRED is a controlled exception,
# not permission for arbitrary backwards movement.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    ApplicationStatus.SUBMITTED.value: {ApplicationStatus.INITIAL_SCRUTINY.value, ApplicationStatus.CORRECTION_REQUIRED.value},
    ApplicationStatus.INITIAL_SCRUTINY.value: {ApplicationStatus.DOCUMENT_VERIFICATION.value, ApplicationStatus.CORRECTION_REQUIRED.value},
    ApplicationStatus.DOCUMENT_VERIFICATION.value: {ApplicationStatus.COMPLIANCE_CHECK.value, ApplicationStatus.CORRECTION_REQUIRED.value},
    ApplicationStatus.COMPLIANCE_CHECK.value: {ApplicationStatus.OFFICER_REVIEW.value, ApplicationStatus.CORRECTION_REQUIRED.value},
    ApplicationStatus.OFFICER_REVIEW.value: {ApplicationStatus.INSPECTION.value, ApplicationStatus.CORRECTION_REQUIRED.value},
    ApplicationStatus.INSPECTION.value: {ApplicationStatus.FINAL_REVIEW.value, ApplicationStatus.CORRECTION_REQUIRED.value},
    ApplicationStatus.FINAL_REVIEW.value: {ApplicationStatus.APPROVED.value, ApplicationStatus.REJECTED.value, ApplicationStatus.CORRECTION_REQUIRED.value},
    ApplicationStatus.CORRECTION_REQUIRED.value: set(),
    ApplicationStatus.APPROVED.value: set(),
    ApplicationStatus.REJECTED.value: set(),
}


def transition_application(db: Session, application: Application, actor: User,
                           to_stage: ApplicationStatus, note: str | None = None) -> Application:
    if actor.role not in {UserRole.OFFICER.value, UserRole.ADMIN.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only officers/admins may change workflow stages")

    current = application.current_stage
    target = to_stage.value
    if current == ApplicationStatus.CORRECTION_REQUIRED.value:
        expected = application.correction_return_stage
        if not expected or target != expected:
            raise HTTPException(status_code=422, detail="Correction must return to the recorded review stage")
        application.correction_return_stage = None
    else:
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise HTTPException(status_code=422, detail=f"Invalid workflow transition: {current} -> {target}")
        if target == ApplicationStatus.CORRECTION_REQUIRED.value:
            application.correction_return_stage = current

    application.current_stage = target
    stage_entry = ApplicationStage(application_id=application.id, from_stage=current, to_stage=target,
                                   changed_by_id=actor.id, note=note)
    db.add(stage_entry)
    append_audit(db, actor_id=actor.id, action="APPLICATION_STAGE_CHANGED", entity_type="application",
                 entity_id=application.id, details={"from_stage": current, "to_stage": target, "note": note})
    db.add(application)
    return application
