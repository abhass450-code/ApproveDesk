from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from app.schemas.alert import AlertCreate


def generate_dedupe_key(alert_type: AlertType, application_id: str, stage_or_rule_id: str, timestamp_str: str = "") -> str:
    """Generates a unique key to prevent duplicate active alerts for the same event."""
    return f"{alert_type.value}:{application_id}:{stage_or_rule_id}:{timestamp_str}"


def create_or_update_alert(db: Session, alert_in: AlertCreate) -> tuple[Alert, bool]:
    """
    Creates a new alert or updates existing matching dedupe_key.
    Returns (alert_instance, is_created_flag)
    """
    existing_alert = db.query(Alert).filter(Alert.dedupe_key == alert_in.dedupe_key).first()

    if existing_alert:
        # If alert exists but was resolved, reopen it; otherwise update message/due date
        if existing_alert.status == AlertStatus.RESOLVED:
            existing_alert.status = AlertStatus.OPEN
            existing_alert.acknowledged_at = None
        existing_alert.message = alert_in.message
        existing_alert.due_at = alert_in.due_at
        db.commit()
        db.refresh(existing_alert)
        return existing_alert, False

    new_alert = Alert(
        application_id=alert_in.application_id,
        recipient_id=alert_in.recipient_id,
        alert_type=alert_in.alert_type,
        severity=alert_in.severity,
        message=alert_in.message,
        due_at=alert_in.due_at,
        dedupe_key=alert_in.dedupe_key,
        status=AlertStatus.OPEN
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return new_alert, True


def create_compliance_failure_alert(db: Session, application_id: str, recipient_id: str, rule_id: str, rule_name: str) -> Alert:
    """Triggered by Member 2 when a compliance check fails."""
    dedupe_key = generate_dedupe_key(AlertType.COMPLIANCE_FAILURE, application_id, rule_id)
    alert_in = AlertCreate(
        application_id=application_id,
        recipient_id=recipient_id,
        alert_type=AlertType.COMPLIANCE_FAILURE,
        severity=AlertSeverity.HIGH,
        message=f"Compliance check failed: {rule_name}",
        dedupe_key=dedupe_key
    )
    alert, _ = create_or_update_alert(db, alert_in)
    return alert


def create_query_overdue_alert(db: Session, application_id: str, recipient_id: str, query_id: str) -> Alert:
    """Triggered when an officer/institution query response is overdue."""
    dedupe_key = generate_dedupe_key(AlertType.QUERY_RESPONSE_OVERDUE, application_id, query_id)
    alert_in = AlertCreate(
        application_id=application_id,
        recipient_id=recipient_id,
        alert_type=AlertType.QUERY_RESPONSE_OVERDUE,
        severity=AlertSeverity.MEDIUM,
        message=f"Query #{query_id} response is past due",
        dedupe_key=dedupe_key
    )
    alert, _ = create_or_update_alert(db, alert_in)
    return alert


def scan_and_create_alerts(db: Session, applications_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, int]:
    """
    Scans application deadlines and generates DEADLINE_SOON or OVERDUE_STAGE alerts.
    Accepts synthetic/mock application data for testing and demo execution.
    """
    now = datetime.now(timezone.utc)
    created_count = 0
    updated_count = 0
    skipped_count = 0

    if applications_data is None:
        applications_data = [
            {
                "id": "APP-DEMO-001",
                "recipient_id": "INST-101",
                "stage": "DOCUMENT_VERIFICATION",
                "due_at": now + timedelta(hours=12),
                "is_completed": False
            },
            {
                "id": "APP-DEMO-002",
                "recipient_id": "OFFICER-202",
                "stage": "SCRUTINY_REVIEW",
                "due_at": now - timedelta(hours=5),
                "is_completed": False
            }
        ]

    for app in applications_data:
        app_id = app["id"]
        recipient_id = app["recipient_id"]
        stage = app["stage"]
        due_at = app["due_at"]
        is_completed = app.get("is_completed", False)

        if is_completed or not due_at:
            skipped_count += 1
            continue

        # Rule 1: Overdue Stage
        if due_at < now:
            dedupe_key = generate_dedupe_key(AlertType.OVERDUE_STAGE, app_id, stage, due_at.strftime("%Y%m%d"))
            alert_in = AlertCreate(
                application_id=app_id,
                recipient_id=recipient_id,
                alert_type=AlertType.OVERDUE_STAGE,
                severity=AlertSeverity.CRITICAL,
                message=f"Stage '{stage}' for application {app_id} is overdue!",
                due_at=due_at,
                dedupe_key=dedupe_key
            )
            _, is_created = create_or_update_alert(db, alert_in)
            if is_created:
                created_count += 1
            else:
                updated_count += 1

        # Rule 2: Approaching Deadline (within 24 hours)
        elif due_at <= now + timedelta(hours=24):
            dedupe_key = generate_dedupe_key(AlertType.DEADLINE_SOON, app_id, stage, due_at.strftime("%Y%m%d"))
            alert_in = AlertCreate(
                application_id=app_id,
                recipient_id=recipient_id,
                alert_type=AlertType.DEADLINE_SOON,
                severity=AlertSeverity.MEDIUM,
                message=f"Deadline approaching for stage '{stage}' (Application {app_id})",
                due_at=due_at,
                dedupe_key=dedupe_key
            )
            _, is_created = create_or_update_alert(db, alert_in)
            if is_created:
                created_count += 1
            else:
                updated_count += 1
        else:
            skipped_count += 1

    return {
        "created_count": created_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count
    }


def acknowledge_alert(db: Session, alert_id: str, recipient_id: str, is_admin: bool = False) -> Optional[Alert]:
    """Marks an open alert as ACKNOWLEDGED with authorization check."""
    query = db.query(Alert).filter(Alert.id == alert_id)
    if not is_admin:
        query = query.filter(Alert.recipient_id == recipient_id)

    alert = query.first()
    if alert:
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)
    return alert