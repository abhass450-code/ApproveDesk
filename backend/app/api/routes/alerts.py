from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models.alert import Alert
from app.models.application import Application
from app.models.user import User
from app.schemas.alert import AlertOut, ScanResultOut
from app.schemas.common import UserRole
from app.services.alert_service import scan_alerts
from app.services.audit_service import append_audit

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _can_see(application: Application, user: User) -> bool:
    if user.role == UserRole.ADMIN.value:
        return True
    if user.role == UserRole.INSTITUTION.value:
        return application.institution_id is not None and application.institution_id == user.institution_id
    if user.role == UserRole.OFFICER.value:
        return application.assigned_officer_id == user.id
    return False


@router.get("", response_model=list[AlertOut])
def list_alerts(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[AlertOut]:
    stmt = (select(Alert).join(Application, Alert.application_id == Application.id)
            .order_by(Alert.created_at.desc()))
    if user.role == UserRole.INSTITUTION.value:
        if user.institution_id is None:
            return []
        stmt = stmt.where(Application.institution_id == user.institution_id)
    elif user.role == UserRole.OFFICER.value:
        from sqlalchemy import or_
        stmt = stmt.where(or_(Application.assigned_officer_id == user.id, Alert.recipient_id == user.id))
    elif user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Insufficient role")
    alerts = db.scalars(stmt.limit(200)).all()
    return [AlertOut.model_validate(alert) for alert in alerts]


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge(alert_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)) -> AlertOut:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    application = db.get(Application, alert.application_id)
    if application is None or not _can_see(application, user):
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.status == "OPEN":
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_at = datetime.now(timezone.utc)
        db.add(alert)
        append_audit(db, actor_id=user.id, action="ALERT_ACKNOWLEDGED", entity_type="alert",
                     entity_id=alert.id, details={"application_id": application.id})
        db.commit()
        db.refresh(alert)
    return AlertOut.model_validate(alert)


@router.post("/scan", response_model=ScanResultOut)
def scan(user: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)) -> ScanResultOut:
    result = scan_alerts(db, user)
    db.commit()
    return ScanResultOut(**result)
