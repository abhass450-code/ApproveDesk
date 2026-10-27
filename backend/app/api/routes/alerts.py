from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertStatus
from app.schemas.alert import AlertRead, ScanResult
from app.services import alert_service

# Placeholder dependency for DB session
def get_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.alert import Base

    engine = create_engine("sqlite:///./alerts.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertRead])
def get_alerts(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_role: Optional[str] = Header("INSTITUTION", alias="X-User-Role"),
    status_filter: Optional[AlertStatus] = None,
    db: Session = Depends(get_db)
):
    """Fetches permitted alerts for current authenticated user/role."""
    query = db.query(Alert)

    # Role visibility check
    if x_user_role != "ADMIN" and x_user_id:
        query = query.filter(Alert.recipient_id == x_user_id)

    if status_filter:
        query = query.filter(Alert.status == status_filter)

    return query.order_by(Alert.created_at.desc()).all()


@router.post("/{alert_id}/acknowledge", response_model=AlertRead)
def acknowledge_alert(
    alert_id: str,
    x_user_id: Optional[str] = Header("DEMO-USER", alias="X-User-ID"),
    x_user_role: Optional[str] = Header("INSTITUTION", alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Acknowledges an active alert."""
    is_admin = (x_user_role == "ADMIN")
    alert = alert_service.acknowledge_alert(db, alert_id, recipient_id=x_user_id or "", is_admin=is_admin)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found or unauthorized to acknowledge."
        )
    return alert


@router.post("/scan", response_model=ScanResult)
def trigger_deadline_scan(
    x_user_role: Optional[str] = Header("ADMIN", alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Admin endpoint to run manual scan on demand for testing/demo."""
    if x_user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN or demo triggers can invoke deadline scans."
        )

    result = alert_service.scan_and_create_alerts(db)
    return result