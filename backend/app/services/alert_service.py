from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.application import Application
from app.models.compliance import ComplianceRule
from app.models.query import Query
from app.models.user import User
from app.services.audit_service import append_audit

TERMINAL_STAGES = {"APPROVED", "REJECTED"}
DEADLINE_SOON_HOURS = 24


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def create_alert(db: Session, *, application_id: int, recipient_id: int | None, alert_type: str,
                 severity: str, message: str, due_at: datetime | None, dedupe_key: str) -> tuple[Alert, bool]:
    """Create an alert unless an unresolved alert with the same dedupe key exists (Member 3 guide Step 7)."""
    existing = db.scalar(select(Alert).where(Alert.dedupe_key == dedupe_key, Alert.status == "OPEN"))
    if existing is not None:
        return existing, False
    alert = Alert(application_id=application_id, recipient_id=recipient_id, alert_type=alert_type,
                  severity=severity, message=message, due_at=due_at, dedupe_key=dedupe_key)
    db.add(alert)
    return alert, True


def create_compliance_failure_alert(db: Session, application: Application, rule: ComplianceRule,
                                    outcome: dict) -> None:
    alert, created = create_alert(
        db, application_id=application.id, recipient_id=application.assigned_officer_id,
        alert_type="COMPLIANCE_FAILURE", severity=rule.severity, due_at=None,
        message=f"{application.application_code}: rule {rule.code} FAILED - {outcome['explanation']}",
        dedupe_key=f"COMPLIANCE_FAILURE:{application.id}:{rule.code}:{rule.version}")
    if created:
        append_audit(db, actor_id=None, action="ALERT_CREATED", entity_type="alert", entity_id=alert.id,
                     details={"alert_type": "COMPLIANCE_FAILURE", "application_id": application.id,
                              "rule_code": rule.code})


def scan_alerts(db: Session, actor: User) -> dict[str, int]:
    """Manual, deterministic scan (Member 3 guide Steps 8, 11). Scheduler is optional later."""
    now = datetime.now(timezone.utc)
    created = skipped = 0

    applications = db.scalars(select(Application).where(Application.due_at.isnot(None))).all()
    for app in applications:
        due = _aware(app.due_at)
        if due is None or app.current_stage in TERMINAL_STAGES:
            continue
        if due <= now:
            _, was_created = create_alert(
                db, application_id=app.id, recipient_id=app.assigned_officer_id,
                alert_type="OVERDUE_STAGE", severity="HIGH", due_at=app.due_at,
                message=f"{app.application_code}: stage {app.current_stage} is overdue (deadline was {due.isoformat()}).",
                dedupe_key=f"OVERDUE_STAGE:{app.id}")
        elif due - now <= timedelta(hours=DEADLINE_SOON_HOURS):
            _, was_created = create_alert(
                db, application_id=app.id, recipient_id=app.assigned_officer_id,
                alert_type="DEADLINE_SOON", severity="MEDIUM", due_at=app.due_at,
                message=f"{app.application_code}: stage {app.current_stage} deadline is due within {DEADLINE_SOON_HOURS} hours.",
                dedupe_key=f"DEADLINE_SOON:{app.id}")
        else:
            continue
        created += 1 if was_created else 0
        skipped += 0 if was_created else 1

    open_queries = db.scalars(select(Query).where(Query.status == "OPEN", Query.due_at.isnot(None))).all()
    for query in open_queries:
        due = _aware(query.due_at)
        if due is None or due > now:
            continue
        app = db.get(Application, query.application_id)
        _, was_created = create_alert(
            db, application_id=query.application_id,
            recipient_id=app.assigned_officer_id if app else None,
            alert_type="QUERY_RESPONSE_OVERDUE", severity="HIGH", due_at=query.due_at,
            message=f"Query #{query.id} on {app.application_code if app else query.application_id} is overdue for a response.",
            dedupe_key=f"QUERY_RESPONSE_OVERDUE:{query.id}")
        created += 1 if was_created else 0
        skipped += 0 if was_created else 1

    append_audit(db, actor_id=actor.id, action="ALERT_SCAN_RUN", entity_type="system",
                 entity_id=None, details={"created": created, "skipped": skipped})
    return {"created": created, "skipped": skipped}
